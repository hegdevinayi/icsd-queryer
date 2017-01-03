# Desired capabilities (initial)
In either 'Basic Search and Retrieve' or 'Chemistry Search' mode:
  * input: 'ICSD Collection Code', output: folder corresponding to the entry, with the CIF file, data parsed from 'Detailed View', and (preferably) a screenshot
  * input: 'Composition' and/or 'Number of Elements', output: folders (with relevant data as above) corresponding to each entry resulting from the query

# Structure of the project
|- LICENSE
|- README.md
|- requirements.txt
|- TODO.md
|- docs
    |-- index.rst
    |-- [other doc files]
|- queryer
    |-- icsdqueryer.py
    |-- [other src files]
|- tests
    |-- test_queryer.py
    |-- [other test files]
|- setup.py
