# Desired capabilities (initial) [COMPLETE]
In either 'Basic Search and Retrieve' or 'Chemistry Search' mode:
  * input: 'ICSD Collection Code', output: folder corresponding to the entry, with the CIF file, data parsed from 'Detailed View', and (preferably) a screenshot
  * input: 'Composition' and/or 'Number of Elements', output: folders (with relevant data as above) corresponding to each entry resulting from the query

# Structure of the project
|- LICENSE
|- README.md
|- requirements.txt
|- NOTES.md
|- queryer.py
|- tags
    |-- query_tags.yml
    |-- parse_tags.yml
|- docs
    |-- index.rst
    |-- [other doc files]
|- tests
    |-- test_queryer.py
    |-- [other test files]
