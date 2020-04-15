import asyncio
import hashlib
import logging
import re
from contextlib import suppress
from json import load
from os.path import dirname, join, getmtime
from time import time
from typing import Optional, Dict, Callable, List, Tuple, Type, Iterable, Set

import aiohttp
from babel import parse_locale
from jinja2 import contextfilter
from jinja2.runtime import resolve_or_missing

from betty.ancestry import Link, Ancestry, HasLinks, Resource
from betty.event import Event
from betty.fs import makedirs
from betty.jinja2 import Jinja2Provider
from betty.locale import Localized, negotiate_locale
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.site import Site


class WikipediaError(BaseException):
    pass  # pragma: no cover


class NotAnEntryError(WikipediaError, ValueError):
    pass  # pragma: no cover


class RetrievalError(WikipediaError, RuntimeError):
    pass  # pragma: no cover


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
    def __init__(self, session: aiohttp.ClientSession, cache_directory_path: str, ttl: int = 86400):
        self._cache_directory_path = join(cache_directory_path, 'wikipedia')
        makedirs(self._cache_directory_path)
        self._ttl = ttl
        self._session = session

    async def _request(self, url: str) -> Dict:
        cache_file_path = join(self._cache_directory_path,
                               hashlib.md5(url.encode('utf-8')).hexdigest())

        response_data = None
        with suppress(FileNotFoundError):
            if getmtime(cache_file_path) + self._ttl > time():
                with open(cache_file_path) as f:
                    response_data = load(f)

        if response_data is None:
            logger = logging.getLogger()
            try:
                async with self._session.get(url) as response:
                    response_data = await response.json()
                    with open(cache_file_path, 'w') as f:
                        f.write(await response.text())
            except aiohttp.ClientError as e:
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

    async def _get_page_data(self, url: str) -> Dict:
        response_data = await self._request(url)
        try:
            return response_data['query']['pages'][0]
        except (LookupError, TypeError) as e:
            raise RetrievalError('Could not successfully parse the JSON format returned by %s: %s' % (url, e))

    async def get_translations(self, entry_language: str, entry_name: str) -> Dict[str, str]:
        url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (
            entry_language, entry_name)
        page_data = await self._get_page_data(url)
        try:
            translations_data = page_data['langlinks']
        except KeyError:
            # There may not be any translations.
            return {}
        return {translation_data['lang']: translation_data['title'] for translation_data in translations_data}

    async def get_entry(self, language: str, name: str) -> Entry:
        url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=extracts&exintro&format=json&formatversion=2' % (
            language, name)
        page_data = await self._get_page_data(url)
        return Entry(language, name, page_data['title'], page_data['extract'])


class Populator:
    def __init__(self, retriever: Retriever):
        self._retriever = retriever

    async def populate(self, ancestry: Ancestry, site: Site) -> None:
        locales = set(site.configuration.locales)
        await asyncio.gather(*[self._populate_resource(resource, site, locales) for resource in ancestry.resources])

    async def _populate_resource(self, resource: Resource, site: Site, locales: Set[str]) -> None:
        if not isinstance(resource, HasLinks):
            return

        entry_links = set()
        for link in resource.links:
            try:
                entry_language, entry_name = parse_url(link.url)
                entry_links.add((entry_language, entry_name))
            except NotAnEntryError:
                continue

            entry = None
            if link.label is None:
                entry = await self._retriever.get_entry(entry_language, entry_name)
            await self.populate_link(link, site, entry_language, entry)

        for entry_language, entry_name in list(entry_links):
            entry_translations = await self._retriever.get_translations(entry_language, entry_name)
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
                    added_entry = await self._retriever.get_entry(added_entry_language, added_entry_name)
                except RetrievalError:
                    continue
                added_link = Link(added_entry.url)
                await self.populate_link(added_link, site, added_entry_language, added_entry)
                resource.links.add(added_link)
                entry_links.add((added_entry_language, added_entry_name))

    async def populate_link(self, link: Link, site: Site, entry_language: str, entry: Optional[Entry] = None) -> None:
        if link.url.startswith('http:'):
            link.url = 'https:' + link.url[5:]
        if link.media_type is None:
            link.media_type = 'text/html'
        if link.relationship is None:
            link.relationship = 'external'
        if link.locale is None:
            link.locale = entry_language
        if link.description is None:
            # There are valid reasons for links in locales that aren't supported.
            with suppress(ValueError):
                async with site.with_locale(link.locale):
                    link.description = _('Read more on Wikipedia.')
        if entry is not None:
            if link.label is None:
                link.label = entry.title


class Wikipedia(Plugin, Jinja2Provider):
    def __init__(self, site: Site):
        self._site = site

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
        self._retriever = Retriever(self._session, self._site.configuration.cache_directory_path)
        self._populator = Populator(self._retriever)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site)

    def subscribes_to(self) -> List[Tuple[Type[Event], Callable]]:
        return [
            (PostParseEvent, self._populate),
        ]

    async def _populate(self, event: PostParseEvent) -> None:
        await self._populator.populate(event.ancestry, self._site)

    @property
    def filters(self) -> Dict[str, Callable]:
        return {
            'wikipedia': self._filter_wikipedia_links,
        }

    @contextfilter
    async def _filter_wikipedia_links(self, context, links: Iterable[Link]) -> Iterable[Entry]:
        locale = parse_locale(resolve_or_missing(context, 'locale'), '-')[0]
        return filter(None, await asyncio.gather(*[self._filter_wikipedia_link(locale, link) for link in links]))

    async def _filter_wikipedia_link(self, locale: str, link: Link) -> Optional[Entry]:
        try:
            entry_language, entry_name = parse_url(link.url)
        except NotAnEntryError:
            return
        if negotiate_locale(locale, [entry_language]) is None:
            return
        try:
            return await self._retriever.get_entry(entry_language, entry_name)
        except RetrievalError:
            return

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
