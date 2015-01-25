#!/usr/bin/env python


import re
import sys
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
            yield m.group(1), parse_date(m.group(3))

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
        # TODO: would be nice to be able to get modified if not passed in
        self.modified = modified
        self.url = 'http://babel.hathitrust.org/cgi/mb?a=listis;c=' + id

        tries = 0
        resp = None
        while tries < 10:
            try:
                resp = http.get(self.url)
                break
            except Exception as e:
                logging.error("unable to fetch %s: %s", url, e)
                tries += 1
        
        if not resp or resp.status_code != 200:
            raise Exception("unable to fetch collection id=%s" % id)

        self.soup = BeautifulSoup(resp.content)
        self.title = self._text('.cn')
        self.owner = self._text('dl[class="collection"] > dd')
        self.description = self._text('.desc > p')
        self.status = self._text('.status')
        self.pages = int(self._text('.PageWidget > li', pos=-2, default=0))

    def jsonld(self): 
        return {
            "dc:title": self.title,
            "dc:creator": self.owner,
            "dc:publisher": "HathiTrust"
        }

    def volumes(self):
        for url in self.volume_urls():
            u = urlparse(url)
            q = parse_qs(u.query)
            yield hathilda.get_volume(q['id'][0])

    def write_csv(self, fh):
        writer = csv.writer(fh)
        writer.writerow(["title", "creator", "issuance", "publisher", "url",
            "contributor1", "contributor2", "contributor3", "contributor4",
            "contributor5", "subject1", "subject2", "subject3", "subject4",
            "subject5", "description1", "description2", "description3",
            "description4", "description5"])

        for item in self.volumes():
            row = [
                item.get('title'),
                item.get('creator'),
                item.get('issuance'),
                item.get('publisher'),
                item['@id'],
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

    def _text(self, q, default='', pos=0):
        text = default
        results = self.soup.select(q)
        if len(results) > 0:
            text = results[pos].text.strip()
        return text

def pad(l1, l2, n):
    if l2 == None:
        l2 = []
    for i in range(0, n):
        if i < len(l2):
            l1.append(l2[i])
        else:
            l1.append(None)

if __name__ == "__main__":
    collection_id = sys.argv[1]
    c = Collection(collection_id)
    c.write_csv(sys.stdout)
