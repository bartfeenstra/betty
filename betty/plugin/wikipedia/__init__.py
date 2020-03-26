import hashlib
import logging
import re
from json import load
from os.path import dirname, join, getmtime
from time import time
from typing import Optional, Dict, Callable, List, Tuple, Type, Iterable

import requests
from babel import parse_locale
from jinja2 import contextfilter
from jinja2.runtime import resolve_or_missing
from requests import RequestException

from betty.ancestry import Link, Ancestry, HasLinks
from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import Jinja2Provider
from betty.locale import Localized, negotiate_locale
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.site import Site


class WikipediaError(BaseException):
    pass


class NotAnEntryError(WikipediaError, ValueError):
    pass


class RetrievalError(WikipediaError, RuntimeError):
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

    def _request(self, url: str) -> Dict:
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
            logger = logging.getLogger()
            try:
                response = requests.get(url)
                response_data = response.json()
                # @todo Why is this makedirs() call necessary? We already do this in self.__init__().
                makedirs(self._cache_directory_path)
                with open(cache_file_path, 'w') as f:
                    f.write(response.text)
            except RequestException as e:
                logger.warning('Could not successfully connect to Wikipedia at %s: %s' % (url, e))
            except ValueError as e:
                logger.warning('Could not parse JSON content from Wikipedia at %s: %s' % (url, e))

        if response_data is None:
            try:
                with open(cache_file_path) as f:
                    response_data = load(f)
            except FileNotFoundError:
                raise RetrievalError('Could neither fetch %s, nor find an old version in the cache.' % url)

        return response_data

    def _get_page_data(self, url: str) -> Dict:
        response_data = self._request(url)
        try:
            return response_data['query']['pages'][0]
        except (LookupError, TypeError):
            raise RetrievalError('Could not successfully parse the JSON format returned by %s.' % url)

    def get_translations(self, entry_language: str, entry_name: str) -> List[Tuple[str, str]]:
        url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (
            entry_language, entry_name)
        page_data = self._get_page_data(url)
        try:
            translations_data = page_data['langlinks']
        except KeyError:
            # There may not be any translations.
            return []
        return [(translation_data['lang'], translation_data['title']) for translation_data in translations_data]

    def get_entry(self, language: str, name: str) -> Entry:
        url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=extracts&exintro&format=json&formatversion=2' % (
            language, name)
        page_data = self._get_page_data(url)
        return Entry(language, name, page_data['title'], page_data['extract'])


class Populator:
    def __init__(self, retriever: Retriever):
        self._retriever = retriever

    def populate(self, ancestry: Ancestry, site: Site) -> None:
        locales = set([configuration.locale for configuration in site.configuration.locales.values()])
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
                    entry = self._retriever.get_entry(entry_language, entry_name)
                self.populate_link(link, site, entry_language, entry)

            for entry_language, entry_name in list(entry_links):
                entry_translations = dict(self._retriever.get_translations(entry_language, entry_name))
                if len(entry_translations) == 0:
                    continue
                entry_languages = list(entry_translations.keys())
                for locale in locales.difference({entry_language}):
                    added_entry_language = negotiate_locale(locale, entry_languages)
                    if added_entry_language is None:
                        continue
                    added_entry_name = entry_translations[added_entry_language]
                    if (added_entry_language, added_entry_name) in entry_links:
                        continue
                    try:
                        added_entry = self._retriever.get_entry(added_entry_language, added_entry_name)
                    except RetrievalError:
                        continue
                    added_link = Link(added_entry.url)
                    self.populate_link(added_link, site, added_entry_language, added_entry)
                    resource.links.add(added_link)
                    entry_links.add((added_entry_language, added_entry_name))

    def populate_link(self, link: Link, site: Site, entry_language: str, entry: Optional[Entry] = None) -> None:
        if link.url.startswith('http:'):
            link.url = 'https:' + link.url[5:]
        if link.media_type is None:
            link.media_type = 'text/html'
        if link.relationship is None:
            link.relationship = 'external'
        if link.locale is None:
            link.locale = entry_language
        if link.description is None:
            try:
                with site.with_locale(link.locale):
                    link.description = _('Read more on Wikipedia.')
            except ValueError:
                # There are valid reasons for links in locales that aren't supported.
                pass
        if entry is not None:
            if link.label is None:
                link.label = entry.title


class Wikipedia(Plugin, Jinja2Provider):
    def __init__(self, site: Site):
        self._site = site
        self._retriever = Retriever(site.configuration.cache_directory_path)
        self._populator = Populator(self._retriever)

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site)

    def subscribes_to(self) -> List[Tuple[Type[Event], Callable]]:
        return [
            (PostParseEvent, lambda event: self._populator.populate(event.ancestry, self._site)),
        ]

    @property
    def filters(self) -> Dict[str, Callable]:
        return {
            'wikipedia': self._filter_wikipedia,
        }

    @contextfilter
    def _filter_wikipedia(self, context, links: Iterable[Link]):
        locale = parse_locale(resolve_or_missing(context, 'locale'), '-')[0]
        for link in links:
            try:
                entry_language, entry_name = parse_url(link.url)
            except NotAnEntryError:
                continue
            if negotiate_locale(locale, [entry_language]) is None:
                continue
            try:
                yield self._retriever.get_entry(entry_language, entry_name)
            except RetrievalError:
                continue

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
