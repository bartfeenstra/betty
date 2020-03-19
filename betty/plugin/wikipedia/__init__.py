import hashlib
import logging
import re
from json import loads
from os.path import dirname
from typing import Iterable, Optional, Dict, Callable
from urllib.parse import urlparse

import requests
from babel import parse_locale
from jinja2 import environmentfilter
from requests import RequestException

from betty.ancestry import Link
from betty.cache import Cache, CacheMissError
from betty.jinja2 import Jinja2Provider
from betty.plugin import Plugin
from betty.site import Site


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


class Retriever:
    def __init__(self, cache: Cache, ttl: int = 86400):
        self._cache = cache
        self._ttl = ttl

    def _request(self, uri: str) -> Optional[Dict]:
        cache_key = hashlib.md5(uri.encode('utf-8')).hexdigest()

        response_data = None
        try:
            response_data = loads(self._cache.get(cache_key, self._ttl))
        except CacheMissError:
            pass

        if response_data is None:
            try:
                response = requests.get(uri)
                response_data = response.json()
                self._cache.set(cache_key, response.text)
            except (RequestException, ValueError) as e:
                logger = logging.getLogger()
                logger.warn(
                    'Could not retrieve content from Wikipedia at %s: %s' % (uri, e))

        if response_data is None:
            try:
                response_data = loads(self._cache.get(cache_key))
            except CacheMissError:
                pass

        return response_data

    def one(self, language: str, link: Link) -> Optional[Entry]:
        parts = urlparse(link.url)
        if parts.scheme not in ['http', 'https']:
            return None
        if not re.fullmatch(r'^[a-z]+\.wikipedia\.org$', parts.netloc, re.IGNORECASE):
            return None
        if not re.fullmatch(r'^/wiki/.+$', parts.path, re.IGNORECASE):
            return None
        link_language, _, _ = parts.netloc.split('.')
        title = parts.path[6:]

        if language != link_language:
            translations_uri = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (
                link_language, title)
            translations_response_data = self._request(translations_uri)
            try:
                translations_data = translations_response_data['query']['pages'][0]['langlinks']
            except (LookupError, TypeError):
                return None
            try:
                title = next(
                    translation_data['title'] for translation_data in translations_data if translation_data['lang'] == language)
            except StopIteration:
                return None
            link_language = language

        page_uri = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=extracts&exintro&format=json&formatversion=2' % (
            link_language, title)
        page_response_data = self._request(page_uri)
        if page_response_data is None:
            return None

        # print(page_response_data['query']['pages'])
        page_data = page_response_data['query']['pages'][0]
        return Entry(link.url, page_data['title'], page_data['extract'])

    def all(self, language: str, links: Iterable[Link]) -> Iterable[Entry]:
        for link in links:
            entry = self.one(language, link)
            if entry is not None:
                yield entry


class Wikipedia(Plugin, Jinja2Provider):
    def __init__(self, retriever: Retriever):
        self._retriever = retriever

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(Retriever(site.cache.with_scope('wikipedia')))

    @property
    def filters(self) -> Dict[str, Callable]:
        return {
            'wikipedia': environmentfilter(lambda environment, links: self._retriever.all(parse_locale(environment.globals['locale'], '-')[0], links)),
        }

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
