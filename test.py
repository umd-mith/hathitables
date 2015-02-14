import sys
import pytest
import logging
import datetime
import hathitables

from six import StringIO
from dateutil.parser import parse as parse_date

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

logging.basicConfig(filename='test.log', level=logging.DEBUG)

def test_collection_ids():
    assert len(list(hathitables.collection_ids())) > 1800

def test_collections():
    c = next(hathitables.collections())
    assert c.modified is not None
    assert type(c.modified) == datetime.datetime 
    assert c.modified.tzinfo

def test_collection():
    c = hathitables.Collection('715130871')
    assert c.id == '715130871'
    assert c.url == 'http://babel.hathitrust.org/cgi/mb?a=listis;c=715130871;sz=100'
    assert c.title == '19-20th C. Psychology Texts-Gen'
    assert c.owner == 'Michael Palij'
    assert c.description == 'A collection of selected psychology books in various areas and from the 19th century to late 20th century (mostly full-view).'
    assert c.status == 'public'
    assert c.pages == 4 

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

def test_metadata(): 
    coll = hathitables.Collection('1761339300')
    meta = coll.metadata()

    assert meta['@context']['@vocab'] == 'http://www.w3.org/ns/csvw#'
    assert meta['@context']['dc'] == 'http://purl.org/dc/terms/'
    assert meta['@context']['dcat'] == 'http://www.w3.org/ns/dcat#'
    assert meta['@context']['prov'] == 'http://www.w3.org/ns/prov#'
    assert meta['@context']['xsd'] == 'http://www.w3.org/2001/XMLSchema#'
    assert meta['@context']['schema'] == 'http://schema.org'

    assert meta['@type'] == 'Table'
    assert meta['dc:title'] == 'Dogen'
    assert meta['dc:description'] == 'Random collection of Dogen books.'
    assert meta['dcat:distribution']['dcat:downloadURL'] == '1761339300.csv'
    assert meta['dc:publisher']['schema:name'] == 'HathiTrust'
    assert meta['dc:publisher']['schema:url'] == 'http://hathitrust.org'

    modified = parse_date(meta['dc:modified'])
    assert modified.year == 2015
    assert modified.month == 1
    assert modified.day == 10

    assert 'tableSchema' in meta
    assert 'columns' in meta['tableSchema']
    cols = meta['tableSchema']['columns']
    assert cols[0]['name'] == 'id'
    assert cols[1]['name'] == 'title'
    assert cols[2]['name'] == 'creator'
    assert cols[3]['name'] == 'issuance'
    assert cols[4]['name'] == 'publisher'
    assert cols[5]['name'] == 'contributor1'
    assert cols[6]['name'] == 'contributor2'
    assert cols[7]['name'] == 'contributor3'
    assert cols[8]['name'] == 'contributor4'
    assert cols[9]['name'] == 'contributor5'
    assert cols[10]['name'] == 'subject1'
    assert cols[11]['name'] == 'subject2'
    assert cols[12]['name'] == 'subject3'
    assert cols[13]['name'] == 'subject4'
    assert cols[14]['name'] == 'subject5'
    assert cols[15]['name'] == 'description1'
    assert cols[16]['name'] == 'description2'
    assert cols[17]['name'] == 'description3'
    assert cols[18]['name'] == 'description4'
    assert cols[19]['name'] == 'description5'
