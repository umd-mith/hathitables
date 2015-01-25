import sys
import pytest
import datetime
import hathitables

from six import StringIO

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

def test_collection_ids():
    assert len(list(hathitables.collection_ids())) > 1800

def test_collections():
    c = next(hathitables.collections())
    assert c.modified is not None
    assert type(c.modified) == datetime.datetime 

def test_collection():
    c = hathitables.Collection('715130871')
    assert c.id == '715130871'
    assert c.url == 'http://babel.hathitrust.org/cgi/mb?a=listis;c=715130871'
    assert c.title == '19-20th C. Psychology Texts-Gen'
    assert c.owner == 'Michael Palij'
    assert c.description == 'A collection of selected psychology books in various areas and from the 19th century to late 20th century (mostly full-view).'
    assert c.status == 'public'
    assert c.pages == 15

    # test that paging works
    count = 0
    for url in c.volume_urls():
        assert 'babel' in url
        count += 1
        if count > 25:
            break
    assert count == 26

def test_volumes():
    coll = hathitables.Collection('1761339300')
    count = 0
    for item in coll.volumes():
        count += 1
        assert '@id' in item
    assert count == 4

def test_csv():
    coll = hathitables.Collection('1761339300')
    fh = StringIO()
    coll.write_csv(fh)
    fh.seek(0)
    count = 0
    for row in csv.DictReader(fh):
        count +=1 
        assert 'title' in row
        assert 'creator' in row
        assert 'issuance' in row
        assert 'subject1' in row
        assert 'contributor1' in row
        assert 'description1' in row
    assert count == 4 
