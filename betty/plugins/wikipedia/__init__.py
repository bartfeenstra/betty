import logging
import re
from os.path import dirname
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests
from requests import RequestException

from betty.ancestry import Link
from betty.jinja2 import Jinja2Provider
from betty.plugin import Plugin


class Entry:
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


def _retrieve_one(link: Link) -> Optional[Entry]:
    parts = urlparse(link.uri)
    if parts.scheme not in ['http', 'https']:
        return None
    if not re.fullmatch(r'^[a-z]+\.wikipedia\.org$', parts.netloc, re.IGNORECASE):
        return None
    if not re.fullmatch(r'^/wiki/.+$', parts.path, re.IGNORECASE):
        return None
    language_code, domain, _ = parts.netloc.split('.')
    title = parts.path[6:]
    uri = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=extracts&exintro&format=json&formatversion=2' % (
        language_code, title)
    try:
        response = requests.get(uri)
    except RequestException as e:
        logger = logging.getLogger()
        logger.warn('Could not connect to Wikipedia: %s' % e)
        return None
    page = response.json()['query']['pages'][0]
    return Entry(link.uri, page['title'], page['extract'])


def _retrieve_all(links: Iterable[Link]) -> Iterable[Entry]:
    for link in links:
        entry = _retrieve_one(link)
        if entry is not None:
            yield entry


class Wikipedia(Plugin, Jinja2Provider):
    @property
    def filters(self):
        return {
            'wikipedia': _retrieve_all,
        }

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
