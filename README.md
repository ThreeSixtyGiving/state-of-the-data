# 360Giving State of the Data

**Author**: Edafe Onerhime

**Last Updated**: 2017-03-29

**Description**:  Creates data for "state of the data" reporting based on data from [datagetter](https://github.com/ThreeSixtyGiving/datagetter).

**Contents**: License, Readme, Python script

## About

This is a prototype script that produces information on publishers and use of fields in [360Giving](http://www.threesixtygiving.org/), a data standard for open standardised grants.

It takes a zip file created by the [data getter scripts](https://github.com/ThreeSixtyGiving/datagetter) and the [360Giving Grant Schema](http://www.threesixtygiving.org/wp-content/plugins/threesixty_docs/standard/schema/360-giving-schema.json)  to produce information used in a dashboard, including:

 1. **Frequency** (*freq_data_YYYY-MM-DD.csv*): The core information - a count of values provided for every field in every file from every publisher, in the schema or not.  This information helps us work out who published what and how much of it (the fill rate).
 2. **Schema** (*schema_data_YYYY-MM-DD.csv*): A list of fields in the schema, their parent object and status (required, recommended or optional). This information helps us work out what's been published, what's missing and which extra fields publishers have added.
 3. **Data** (*data_all_data_YYYY-MM-DD.csv*): A list of files and publishers, including if the file was valid against the schema and openly licensed. This information helps us work out which publishers to approach to fix their files.
 4. **Metadata** (*metadata_YYYY-MM-DD.csv*): A spreadsheet version of the [360Giving data registry](http://data.threesixtygiving.org/data.json) that lists all the files currently shared by organisations publishing to the standard. This information helps us understand what's currently available and if the information in the data spreadsheet is out of date.

## Instructions

 - Run [datagetter](https://github.com/ThreeSixtyGiving/datagetter) locally or copy a tarball output file.
 - Clone or download this repo.
 - In a terminal or command window, navigate to the repo
 - Run the command: python sotd.py --tar "*path to tarball*" --schema "http://standard.threesixtygiving.org/en/latest/_static/360-giving-schema.json"

The script will extract JSON files from the tarball - these are spreadsheets and other files downloaded from the data registry and converted to JSON.

Next, the script downloads the 360Giving JSON schema and flattens it into a spreadsheet. Then it processes each publisher's JSON file to produce the frequency information. Each file (Frequency, Schema, Data and Metadata) is created and the JSON files are archived, unless the --archive flag is FALSE.

You can now use the files for analysis or manually copy the information into the State of the Data Prototype dashboard.

## Things to note

 1. Each file (Frequency, Schema, Data and Metadata) gets a date - this is the date from the datagetter tarball.
 2. 360Giving allows [more than one occurrence](http://www.threesixtygiving.org/standard/reference/#toc-one-to-many-relationships) for some fields per grant. For example, if a grant has 3 classifications, the publisher can provide each classification as a separate column or provide a new sheet with each classification as a new row. For one-to-many relationships, the script will count all values as a single column. This means a publisher could publish more classifications than grants.

## Things to do

 1. Better representation of [one-to-many relationships](http://www.threesixtygiving.org/standard/reference/#toc-one-to-many-relationships) so that it's obvious who is publishing one-to-many information.
 2. Add this script to the datagetter workflow so that it gets run monthly.
 3. Link this script to the dashboard so that updating the dashboard isn't a manual job.
 4. Publish the files (Frequency, Schema, Data and Metadata)  as open data so that interested people can re-use the information.
