import pytest
import hathitables

def test_collection_ids():
    assert len(list(hathitables.collection_ids())) > 1800

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
    for url in c.record_urls():
        assert 'babel' in url
        count += 1
        if count > 25:
            break
    assert count == 26
