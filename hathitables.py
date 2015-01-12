#!/usr/bin/env python

import re
import hathilda
import requests
import unicodecsv

from urlparse import urljoin
from bs4 import BeautifulSoup
from urlparse import urlparse, urljoin, parse_qs

def collections():
    """
    Get a list of all public collections at HathiTrust.
    """
    for coll_id in collection_ids():
        yield Collection(coll_id)

def collection_ids():
    """
    Get a list of identifiers for all public HathiTrust collections.
    """
    resp = requests.get("http://babel.hathitrust.org/cgi/mb?colltype=updated")
    if resp.status_code == 200:
        patt = re.compile("\[\];\n +html.push\('(\d+)'\);", re.MULTILINE) 
        for id in re.findall(patt, resp.content):
            yield id

class Collection():
    """
    A class that represents a HathiTrust collection. An instance of
    Collection will let you get metadata for a collection and then get
    metadata for each item in the collection. You can also write out CSV
    for the collection.
    """

    def __init__(self, id):
        """
        Create a HathiTrust collection using its identifier at hathitrust.org.
        """

        self.url = 'http://babel.hathitrust.org/cgi/mb?a=listis;c=' + id
        resp = requests.get(self.url)
        if resp.status_code != 200:
            raise Exception("unable to fetch collection id=%s" % id)

        self.soup = BeautifulSoup(resp.content)
        self.title = self._text('.cn')
        self.owner = self._text('dl[class="collection"] > dd')
        self.description = self._text('.desc > p')
        self.status = self._text('.status')
        self.pages = int(self._text('.PageWidget > li', pos=-2, default=0))

    def items(self):
        for url in self.item_urls():
            u = urlparse(url)
            q = parse_qs(u.query)
            yield hathilda.get_volume(q['id'][0])

    def write_csv(self, fh):
        csv = unicodecsv.writer(fh)
        csv.writerow(["url", "title"])
        for item in self.items():
            csv.writerow([
                item['@id'],
                item['title']
            ])

    def item_urls(self):
        for pg in range(1, self.pages + 1):
            url = self.url + ';sort=title_a;pn=%i;sz=100' % pg
            resp = requests.get(url)
            soup = BeautifulSoup(resp.content)
            for link in soup.select('.result-access-link'):
                yield urljoin(url, link.select('li > a')[-1]['href'])

    def _text(self, q, default='', pos=0):
        text = default
        results = self.soup.select(q)
        if len(results) > 0:
            text = results[pos].text.strip()
        return text

if __name__ == "__main__":
    for c in collections():
        print c.title
        break
