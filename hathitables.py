#!/usr/bin/env python

"""
hathitables is a module for working with HathiTrust collections as CSV.
"""


import re
import sys
import json
import pytz
import logging
import argparse
import hathilda
import requests

from six import StringIO
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from six.moves.urllib.parse import urlparse, urljoin, parse_qs

from requests.adapters import HTTPAdapter

# retry fetches that fail

http = requests.Session()
http.mount('http://babel.hathitrust.org', HTTPAdapter(max_retries=10))
http.mount('http://catalog.hathitrust.org', HTTPAdapter(max_retries=10))

# only need unicodecsv for python2

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

def collections():
    """
    A generator that returns all public collections at HathiTrust in 
    order of their last update.
    """
    for coll_id, modified in collection_ids():
        c = Collection(id=coll_id, modified=modified)
        yield c

def collection_ids():
    """
    A generator for id, last modified values for each collection.
    """
    # kinda fragile, obviously :)
    patt = re.compile("html = \[\];.+?html.push\('(.+?)'\).+?html.push\('(.+?)'\).+?html.push\('(.+?)'\)", re.MULTILINE | re.DOTALL)
    resp = http.get("http://babel.hathitrust.org/cgi/mb?colltype=updated")
    if resp.status_code == 200:
        for m in re.finditer(patt, resp.content.decode('utf8')):
            # no timezone info, so we force UTC
            t = parse_date(m.group(3))
            t = t.replace(tzinfo=pytz.UTC)
            yield m.group(1), t

class Collection():
    """
    A class that represents a HathiTrust collection. An instance of
    Collection will let you get metadata for a collection and then get
    metadata for each item in the collection. You can also write out CSV
    for the collection.
    """

    def __init__(self, id, modified=None):
        """
        Create a HathiTrust collection using its identifier at hathitrust.org.
        """
        self.id = id
        self.modified = modified or self._get_modified()

        self.url = 'http://babel.hathitrust.org/cgi/mb?a=listis;c=%s;sz=100' % id
        resp = http.get(self.url)
        logging.info("fetching collection %s", id)
        
        if not resp or resp.status_code != 200:
            logging.error("received %s when fetching %s", resp.status_code, id)
            raise Exception("unable to fetch collection id=%s" % id)

        self.soup = BeautifulSoup(resp.content)
        self.title = self._text('.cn')
        self.owner = self._text('dl[class="collection"] > dd')
        self.description = self._text('.desc > p')
        self.status = self._text('.status')
        self.pages = int(self._text('.PageWidget > li', pos=-2, default=0))

    def volumes(self):
        for url in self.volume_urls():
            u = urlparse(url)
            q = parse_qs(u.query)
            vol_id = q['id'][0]
            logging.info("fetching volume %s", vol_id)
            vol = hathilda.get_volume(vol_id)
            if vol:
                yield vol
            else:
                logging.error("unable to get volume %s", vol_id)

    def write_metadata(self, fh):
        fh.write(json.dumps(self.metadata(), indent=2))

    def write_csv(self, fh):
        writer = csv.writer(fh)
        writer.writerow(["id", "title", "creator", "issuance", "publisher",
            "contributor1", "contributor2", "contributor3", "contributor4",
            "contributor5", "subject1", "subject2", "subject3", "subject4",
            "subject5", "description1", "description2", "description3",
            "description4", "description5"])

        for item in self.volumes():
            vol_id = item['@id'].split('/')[-1]
            row = [
                vol_id,
                item.get('title'),
                item.get('creator'),
                item.get('issuance'),
                item.get('publisher'),
            ]
            pad(row, item.get('contributor'), 5)
            pad(row, item.get('subject'), 5)
            pad(row, item.get('description'), 5)
            writer.writerow(row)

    def volume_urls(self):
        for pg in range(1, self.pages + 1):
            url = self.url + ';sort=title_a;pn=%i;sz=100' % pg
            resp = http.get(url)
            soup = BeautifulSoup(resp.content)
            for link in soup.select('.result-access-link'):
                yield urljoin(url, link.select('li > a')[-1]['href'])

    def metadata(self): 
        """
        Returns CSVW metadata for the collection as JSON-LD.
        """
        meta = {
            "@context": {
                "@vocab": "http://www.w3.org/ns/csvw#",
                "dc": "http://purl.org/dc/terms/",
                "dcat": "http://www.w3.org/ns/dcat#",
                "prov": "http://www.w3.org/ns/prov#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "schema": "http://schema.org"
            },
            "@type": "Table",
            "dc:title": self.title,
            "dc:creator": self.owner,
            "dc:publisher": {
                "schema:name": "HathiTrust",
                "schema:url": "http://hathitrust.org"
            },
            "dcat:distribution": {
                "dcat:downloadURL": "%s.csv" % self.id
            },
            "tableSchema": {
                "primaryKey": "id",
                "aboutUrl": "http://hdl.handle.net/2027/{id}",
                "columns": [
                    {
                        "name": "id",
                        "required": True,
                        "unique": True
                    },
                    {
                        "name": "title",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/title"
                    },
                    {
                        "name": "creator",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/creator"
                    },
                    {
                        "name": "issuance",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/issuance"
                    },
                    {
                        "name": "publisher",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/publisher"
                    },
                    {
                        "name": "contributor1",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/contributor"
                    },
                    {
                        "name": "contributor2",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/contributor"
                    },
                    {
                        "name": "contributor3",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/contributor"
                    },
                    {
                        "name": "contributor4",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/contributor"
                    },
                    {
                        "name": "contributor5",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/contributor"
                    },
                    {
                        "name": "subject1",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/subject"
                    },
                    {
                        "name": "subject2",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/subject"
                    },
                    {
                        "name": "subject3",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/subject"
                    },
                    {
                        "name": "subject4",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/subject"
                    },
                    {
                        "name": "subject5",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/subject"
                    },
                    {
                        "name": "description1",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/description"
                    },
                    {
                        "name": "description2",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/description"
                    },
                    {
                        "name": "description3",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/description"
                    },
                    {
                        "name": "description4",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/description"
                    },
                    {
                        "name": "description5",
                        "datatype": "string",
                        "propertyUrl": "http://purl.org/dc/terms/description"
                    }
                ]
            }
        }

        if self.description:
            meta['dc:description'] = self.description

        if self.modified: 
            meta['dc:modified'] = self.modified.strftime("%Y-%m-%dT%H:%M:%SZ")

        return meta


    def _text(self, q, default='', pos=0):
        text = default
        results = self.soup.select(q)
        if len(results) > 0:
            text = results[pos].text.strip()
        return text

    def _get_modified(self, no_cache=False):
        """
        Returns the last modified time for the collection. The value
        can be returned from a cache unless no_cache is True.
        """
        if no_cache or not hasattr(Collection, "_modified"):
            Collection._modified = {}
            for id, modified in collection_ids():
                Collection._modified[id] = modified
        return Collection._modified.get(self.id)


def pad(l1, l2, n):
    if l2 == None:
        l2 = []
    for i in range(0, n):
        if i < len(l2):
            l1.append(l2[i])
        else:
            l1.append(None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("collection_id", help="the HathiTrust collection id")
    parser.add_argument("--metadata", action="store_true", help="output collection metadata as json")
    args = parser.parse_args()

    c = Collection(args.collection_id)
    if args.metadata:
        c.write_metadata(sys.stdout)
    else:
        c.write_csv(sys.stdout)
