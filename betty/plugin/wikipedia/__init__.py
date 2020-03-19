import hashlib
import logging
import re
from json import load
from os.path import dirname, join, getmtime
from time import time
from typing import Iterable, Optional, Dict, Callable, List, Tuple, Type

import requests
from babel import parse_locale
from jinja2 import contextfilter
from jinja2.runtime import resolve_or_missing
from requests import RequestException

from betty.ancestry import Link, Ancestry, HasLinks
from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import Jinja2Provider
from betty.locale import Localized
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.site import Site


class NotAnEntryError(ValueError):
    pass


_URL_PATTERN = re.compile(r'^https?://([a-z]+)\.wikipedia\.org/wiki/([^/?#]+).*$')


def parse_url(url: str) -> Tuple[str, str]:
    match = _URL_PATTERN.fullmatch(url)
    if match is None:
        raise NotAnEntryError
    return match.groups()


class Entry(Localized):
    def __init__(self, locale: str, name: str, title: str, content: str):
        Localized.__init__(self, locale)
        self._name = name
        self._title = title
        self._content = content

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return 'https://%s.wikipedia.org/wiki/%s' % (self.locale, self._name)

    @property
    def title(self) -> str:
        return self._title

    @property
    def content(self) -> str:
        return self._content


class Retriever:
    def __init__(self, cache_directory_path: str, ttl: int = 86400):
        self._cache_directory_path = join(cache_directory_path, 'wikipedia')
        makedirs(self._cache_directory_path)
        self._ttl = ttl

    def _request(self, url: str) -> Optional[Dict]:
        cache_file_path = join(self._cache_directory_path,
                               hashlib.md5(url.encode('utf-8')).hexdigest())

        response_data = None
        try:
            if getmtime(cache_file_path) + self._ttl > time():
                with open(cache_file_path) as f:
                    response_data = load(f)
        except FileNotFoundError:
            pass

        if response_data is None:
            try:
                response = requests.get(url)
                response_data = response.json()
                with open(cache_file_path, 'w') as f:
                    f.write(response.text)
            except (RequestException, ValueError) as e:
                logger = logging.getLogger()
                logger.warning(
                    'Could not retrieve content from Wikipedia at %s: %s' % (url, e))

        if response_data is None:
            try:
                with open(cache_file_path) as f:
                    response_data = load(f)
            except FileNotFoundError:
                pass

        return response_data

    def for_entry(self, entry_language: str, entry_name: str, locale: str) -> Optional[Entry]:
        if locale != entry_language:
            translations_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (
                entry_language, entry_name)
            translations_response_data = self._request(translations_url)
            try:
                translations_data = translations_response_data['query']['pages'][0]['langlinks']
            except (LookupError, TypeError):
                return None
            try:
                # @todo Negotiate locales/languages instead of doing a mere equality check.
                entry_name = next(
                    translation_data['title'] for translation_data in translations_data if translation_data['lang'] == locale)
            except StopIteration:
                return None

        page_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=extracts&exintro&format=json&formatversion=2' % (
            locale, entry_name)
        page_response_data = self._request(page_url)
        if page_response_data is None:
            return None

        page_data = page_response_data['query']['pages'][0]
        return Entry(entry_language, entry_name, page_data['title'], page_data['extract'])

    def for_resource(self, resource: HasLinks, locale: str) -> Iterable[Entry]:
        for link in resource.links:
            try:
                entry_language, entry_name = parse_url(link.url)
                entry = self.for_entry(entry_language, entry_name, locale)
                if entry is not None:
                    yield entry
            except NotAnEntryError:
                pass


class Wikipedia(Plugin, Jinja2Provider):
    def __init__(self, site: Site, retriever: Retriever):
        self._site = site
        self._retriever = retriever

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site, Retriever(site.configuration.cache_directory_path))

    def subscribes_to(self) -> List[Tuple[Type[Event], Callable]]:
        return [
            (PostParseEvent, lambda event: self._populate_ancestry(event.ancestry)),
        ]

    @property
    def filters(self) -> Dict[str, Callable]:
        @contextfilter
        def _filter_wikipedia(context, resource):
            language = parse_locale(resolve_or_missing(context, 'locale'), '-')[0]
            return self._retriever.for_resource(resource, language)

        return {
            'wikipedia': _filter_wikipedia,
        }

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)

    def _populate_ancestry(self, ancestry: Ancestry) -> None:
        locales = set([configuration.locale for configuration in self._site.configuration.locales.values()])
        for resource in ancestry.resources:
            if not isinstance(resource, HasLinks):
                continue

            entry_links = set()
            for link in resource.links:
                try:
                    entry_language, entry_name = parse_url(link.url)
                    entry_links.add((entry_language, entry_name))
                except NotAnEntryError:
                    continue

                entry = None
                if link.label is None:
                    entry = self._retriever.for_entry(entry_language, entry_name, entry_language)
                self._populate_link(link, entry)

            for entry_language, entry_name in entry_links:
                for locale in locales.difference({entry_language}):
                    entry = self._retriever.for_entry(entry_language, entry_name, locale)
                    if entry is None:
                        continue
                    if (entry.locale, entry.name) in entry_links:
                        continue
                    link = Link(entry.url)
                    self._populate_link(link, entry)

    def _populate_link(self, link: Link, entry: Optional[Entry] = None) -> None:
        if link.url.startswith('http:'):
            link.url = 'https:' + link.url[5:]
        if link.locale is None:
            link.locale = entry.locale
        if link.media_type is None:
            link.media_type = 'text/html'
        if link.description is None:
            with self._site.with_locale(link.locale):
                link.description = _('Read more on Wikipedia.')
        if entry is not None:
            if link.label is None:
                link.label = entry.title
