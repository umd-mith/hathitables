#!/usr/bin/env python

import re
import requests

from urlparse import urljoin
from bs4 import BeautifulSoup

def collections():
    for coll_id in collection_ids():
        yield Collection(coll_id)

def collection_ids():
    resp = requests.get("http://babel.hathitrust.org/cgi/mb?colltype=updated")
    if resp.status_code == 200:
        patt = re.compile("\[\];\n +html.push\('(\d+)'\);", re.MULTILINE) 
        for id in re.findall(patt, resp.content):
            yield id

class Collection():

    def __init__(self, id):
        self.id = id

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

    def record_urls(self):
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
