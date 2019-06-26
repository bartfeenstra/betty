from typing import Iterable
from urllib.parse import urlparse

import requests

from betty.ancestry import Link
from betty.jinja2 import Jinja2Provider
from betty.plugin import Plugin


class WikipediaEntry:
    def __init__(self, uri: str, title: str, content: str):
        self._uri = uri
        self._title = title
        self._content = content

    @property
    def uri(self):
        return self._uri

    @property
    def title(self):
        return self._title

    @property
    def content(self):
        return self._content


def _retrieve_one(link: Link) -> WikipediaEntry:
    parts = urlparse(link.uri)
    language_code, domain, _ = parts.netloc.split('.')
    if not parts.path.startswith('/wiki/'):
        # @todo We must ignore any link that does not point to a Wikipedia entry.
        raise ValueError
    title = parts.path[6:]
    uri = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=extracts&format=json&formatversion=2' % (
        language_code, title)
    response = requests.get(uri)
    page = response.json()['query']['pages'][0]
    return WikipediaEntry(link.uri, page['title'], page['extract'])


def _retrieve_all(links: Iterable[Link]) -> Iterable[WikipediaEntry]:
    for link in links:
        yield _retrieve_one(link)


class Wikipedia(Plugin, Jinja2Provider):
    @property
    def filters(self):
        return {
            'wikipedia': _retrieve_all,
        }
