[![Build Status](https://travis-ci.org/umd-mith/hathitables.svg)](http://travis-ci.org/umd-mith/hathitables)

hathitables demonstrates how HathiTrust collections can be shared as 
Linked Data friendly CSV a.k.a. [CSV on the Web](https://w3c.github.io/csvw/).

More context for this work can be found at MITH's page for the 
[HathiTrust Workset Creation for Scholarly Analysis](http://mith.umd.edu/research/project/workset-creation-for-scholarly-analysis-project/) project.

## Use

If you want to get csv for a given HathiTrust collection you can use
hathitables on the command line:

    hathitables.py 1761339300

If you'd rather use it programatically from Python you can do this:

```python
import hathitables

coll = hathitables.Collection('1761339300')
for vol in coll.volumes():
    print vol['title']
```

