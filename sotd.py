"""
    Creates data for "state of the data" reporting
    Based on data produced in https://github.com/ThreeSixtyGiving/datagetter
    
    Author:  Edafe Onerhime
    Created: 2017-03-26
    Python Version: 3.5.3
"""    

import os
import json
import ijson
import errno
import shutil
import tarfile
import argparse
import pandas as pd
from glob import glob
import urllib.request
from collections import defaultdict

def checkParams(tarPath, schemaPath):
    """ 
        Checks the supplied parameters are valid
        To do: Better checks on the paths than looking for http
    """    
    
    # Check Params    
    if tarPath is None or not (os.path.isfile(str(tarPath)) or "http" in str(tarPath)):
        print("Error: tar file not found")
        return False
    if schemaPath is None or not (os.path.isfile(str(schemaPath)) or "http" in str(schemaPath)):
        print("Error: Schema not found")
        return False                
    return True

def get_members(tar, prefix):
    """
        Extracts file from folder in tarball
    """
        
    if not prefix.endswith('/'):
        prefix += '/'
    offset = len(prefix)
    for tarinfo in tar.getmembers():
        if tarinfo.name.startswith(prefix):
            tarinfo.name = tarinfo.name[offset:]
            yield tarinfo
            
def getTar(tarPath):
    """
        Extracts to data folder: 
            1. json_all folder
            2. data_all.json
    """
    
    try:
        if os.path.isdir("data"):
            shutil.rmtree("data")
        tar = tarfile.open(tarPath)
        tar.extract("data/data_all.json")    
        tar.extractall(path=os.path.join("data","json_all"),members=get_members(tar, "data/json_all/"))
    except:
        return False
    return True

def getSchema(schemaPath, localSchema):
    """
        Downloads the 360Giving schema
    """
    try:
        if not os.path.isfile(localSchema):
            urllib.request.urlretrieve(schemaPath, localSchema)                
    except:
        return False
    return True

def getSchemaFields(localSchema, recommendedFields):
    """
        Gets all the fields from the 360Giving schema.
        Adds parent, parent's weight and field's weight.
        Adds Required, Recommended, Optional as weights 0 - 100 in Optional
        Returns sorted dataframe
    """
    
    schemaSort = []    
    try:
        # Load JSON
        with open(localSchema,'r') as f:
            schema = json.load(f)      
        
        # Loop through properties    
        for parentItem in schema["properties"]:
            # Parents
            if parentItem in schema["required"]:
                optWt = 0
            elif parentItem in recommendedFields:
                optWt = 50
            else:
                optWt = 100           
            if "weight" in schema["properties"][parentItem]:
                parentWt = schema["properties"][parentItem]["weight"] + optWt
            elif parentItem in schema["definitions"]:
                if "weight" in schema["definitions"][parentItem]:
                    parentWt = schema["definitions"][parentItem]["weight"] + optWt
                else:
                    parentWt = 99 + optWt
            else:
                parentWt = 100 + optWt
            
            # Children
            if not "items" in schema["properties"][parentItem]:
                # Add the parent
                schemaSort.append([parentItem, parentItem, parentWt, parentWt, optWt])
            elif not "$ref" in schema["properties"][parentItem]["items"]:
                # Add the parent
                schemaSort.append([parentItem, parentItem, parentWt, parentWt, optWt])                               
            else:
                # Add the children
                defItem = schema["properties"][parentItem]["items"]["$ref"].split("/")[-1]
                if defItem in schema["definitions"]:
                    if "properties" in schema["definitions"][defItem]:
                        for childItem in schema["definitions"][defItem]["properties"]:                                
                            if "weight" in schema["definitions"][defItem]["properties"][childItem]:
                                childWt = (schema["definitions"][defItem]["properties"][childItem]["weight"])/1000
                            elif childItem in schema["definitions"]:
                                if "weight" in schema["definitions"][childItem]:
                                    childWt = (schema["definitions"][childItem]["weight"]/1000)
                                else:
                                    childWt =  0.099
                            else:
                                childWt = 0.1
                            schemaSort.append([parentItem+"."+childItem, parentItem, parentWt, childWt, optWt])  

        # Create and sort dataframe                            
        df = pd.DataFrame(schemaSort, columns=["Fields","Parent","ParentWeight","Weight", "OptionalWeight"])
        df.set_index("Fields", inplace=True)
        df.sort_values(["ParentWeight","Parent","Weight"], inplace = True)                                      
    except:
        return None
    return df

def flattenJson(jsonString, delimiter):
    """
        Flattens a Json string
    """
    try:
        val = {}
        for i in jsonString.keys():
            if isinstance(jsonString[i], list):
                for l in jsonString[i]:
                    get = flattenJson(l, delimiter)
                    for j in get.keys():                
                        val[ i + delimiter + j ] = get[j]
            elif isinstance(jsonString[i], dict):
                get = flattenJson(jsonString[i], delimiter)
                for j in get.keys():
                    val[ i + delimiter + j ] = get[j]
            else:
                val[i] = jsonString[i]
    except:
        return None
    return val
    
def getDataAllFields(dataAllFile):
    """
        Get data_all: contains summary information about the data load from dataGetter.
    """
    try:
        flattenAll = []    
        with open(dataAllFile,'r') as f:
            dataAll = json.load(f)
        if isinstance(dataAll, list):
            for entry in dataAll:
                flattenAll.append(flattenJson(entry,'.'))
        else:
            flattenAll.append(flattenJson(dataAll,'.'))
        df = pd.DataFrame.from_records(flattenAll, index="identifier")                                           
    except:
        return None        
    return df    

def getColumnFields(jsonFiles, dfAll, dfSchema):
    """
        Get column fill rate and metadata
    """
    pathSep = os.path.sep
    metaData = []
    dfFreq = pd.DataFrame(index=["Fields"], columns=["Parent","ParentWeight","Weight", "OptionalWeight", "In Schema"])
    dfMeta = pd.DataFrame(columns=["Identifier","Publisher","Downloaded","License","Prefix","Title","Type","Valid"])
    
    for j in jsonFiles:
        jsonFile = open(j, "r")        
        parser = ijson.parse(jsonFile)
        keyList = []
        eventList = []
        identifier = j.replace(".json","").split(pathSep)[-1]
        publisher = dfAll.loc[identifier,"publisher.name"]

        for prefix,event,value in parser:
            eventList.append(event)
            if event not in ("end_map", "end_array", "start_map", "map_key", "start_array"):
                keyList.append(prefix.replace("grants.item.","").replace(".item","")) 
        keyFreq = defaultdict(lambda: 0)
        for key in keyList:
            keyFreq[key] += 1
        keyFreq = dict(keyFreq)
        metaData.append([identifier, publisher, dfAll.loc[identifier,"datagetter_metadata.datetime_downloaded"], dfAll.loc[identifier,"datagetter_metadata.acceptable_license"], dfAll.loc[identifier,"publisher.prefix"], dfAll.loc[identifier,"distribution.title"], dfAll.loc[identifier,"datagetter_metadata.file_type"], dfAll.loc[identifier,"datagetter_metadata.valid"]])

        # Create dataframes
        df = pd.DataFrame(list(keyFreq.items()), columns=["Fields", identifier])
        df.set_index("Fields", inplace=True)
        dfFreq = dfFreq.add(df, fill_value=0)            
            
    # Add sort fields and sort. Create Metadata
    dfFreq["Parent"] = dfSchema["Parent"]
    dfFreq["ParentWeight"] = dfSchema["ParentWeight"]
    dfFreq["Weight"] = dfSchema["Weight"]
    dfFreq["OptionalWeight"] = dfSchema["OptionalWeight"]
    dfFreq["In Schema"] = dfFreq.apply(lambda row: pd.notnull(row["Weight"]), axis=1)
    dfFreq["Fields"] = dfFreq.index
    cols = dfFreq.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    dfFreq = dfFreq[cols]
    dfFreq.sort_values(["ParentWeight","Parent","Weight","Fields"], inplace = True)    
    dfMeta = pd.DataFrame(metaData, columns = dfMeta.columns.values.tolist())    
    return dfMeta, dfFreq
  
def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--tar", help="Path to the tar file")
    parser.add_argument("--schema", help="URL or Path to the schema (default=http://standard.threesixtygiving.org/en/latest/_static/360-giving-schema.json)", default="http://standard.threesixtygiving.org/en/latest/_static/360-giving-schema.json")
    args = parser.parse_args()

    # Exit early if parameters aren't properly supplied
    if not checkParams(args.tar, args.schema):
        return False
    
    # Variables
    tarPath = args.tar
    schemaPath = args.schema
    localSchema = "360-giving-schema.json"
    dataAllFile = os.path.join("data","data_all.json")
    recommendedFields = ["grantProgramme","beneficiaryLocation","dataSource", "dateModified"]
       
    # Exit if we can't get the files
    if not getTar(tarPath):
        print("Error: Getting tar files")
        return False        
    if not getSchema(schemaPath, localSchema):
        print("Error: Getting schema files")
        return False            
        
    # Exit if we can't get fields
    dfSchema = getSchemaFields(localSchema,recommendedFields)
    if dfSchema is None:
        print("Error: Getting schema fields")
        return False  
    dfAll = getDataAllFields(dataAllFile)            
    if dfAll is None:
        print("Error: Getting Data All fields")
        return False  

    jsonFiles = glob(os.path.join("data","json_all","*.json"))

    dfMeta, dfFreq = getColumnFields(jsonFiles, dfAll, dfSchema)
    if dfMeta is None or dfFreq is None:
        print("Error: Getting metadata and frequency fields")
        return False  
    dfMeta.to_csv(os.path.join("data","meta.csv"),index=False)                
    dfSchema.to_csv(os.path.join("data","schema.csv"),index=False)
    dfAll.to_csv(os.path.join("data","data_all.csv"),index=False)
    dfFreq.to_csv(os.path.join("data","freq.csv"),index=False)    
if __name__ == "__main__":
    main()     
