[![Build Status](https://travis-ci.org/umd-mith/hathitables.svg)](http://travis-ci.org/umd-mith/hathitables)

hathitables demonstrates how HathiTrust collections can be shared as 
Linked Data friendly CSV a.k.a. [CSV on the Web](https://w3c.github.io/csvw/).

More context for this work can be found at MITH's page for the 
[HathiTrust Workset Creation for Scholarly Analysis](http://mith.umd.edu/research/project/workset-creation-for-scholarly-analysis-project/) project.

If you want to get CSV for a given HathiTrust collection you can use
hathitables on the command line:

    % hathitables.py 1761339300 > 1761339300.csv
    % hathitables.py --metadata 1761339300 > 1761339300.csv-metadata.json

If you want you can also use hathitables programatically from Python:

```python
import hathitables

collection = hathitables.Collection('1761339300')

collection.write_csv(open("file.csv", "w"))
collection.write_json(open("file.csv-metadata.json", "w"))
```

