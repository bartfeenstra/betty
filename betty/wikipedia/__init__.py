import asyncio
import hashlib
import json
import logging
import re
from contextlib import suppress
from os.path import getmtime
from pathlib import Path
from time import time
from typing import Optional, Dict, Callable, Tuple, Iterable, Set

import aiofiles
import aiohttp
from jinja2 import pass_context
from jinja2.runtime import Context
from reactives import reactive

from betty.app import App, Extension
from betty.asyncio import sync
from betty.gui import GuiBuilder
from betty.jinja2 import Jinja2Provider
from betty.load import PostLoader
from betty.locale import Localized, negotiate_locale
from betty.media_type import MediaType
from betty.model.ancestry import Link, HasLinks, Entity


class WikipediaError(BaseException):
    pass  # pragma: no cover


class NotAnEntryError(WikipediaError, ValueError):
    pass  # pragma: no cover


class RetrievalError(WikipediaError, RuntimeError):
    pass  # pragma: no cover


_URL_PATTERN = re.compile(r'^https?://([a-z]+)\.wikipedia\.org/wiki/([^/?#]+).*$')


def _parse_url(url: str) -> Tuple[str, str]:
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


class _Retriever:
    def __init__(self, http_client: aiohttp.ClientSession, cache_directory_path: Path, ttl: int = 86400):
        self._cache_directory_path = cache_directory_path / 'wikipedia'
        self._cache_directory_path.mkdir(exist_ok=True, parents=True)
        self._ttl = ttl
        self._http_client = http_client

    async def _request(self, url: str) -> Dict:
        cache_file_path = self._cache_directory_path / hashlib.md5(url.encode('utf-8')).hexdigest()

        response_data = None
        with suppress(FileNotFoundError):
            if getmtime(cache_file_path) + self._ttl > time():
                async with aiofiles.open(cache_file_path, encoding='utf-8') as f:
                    json_data = await f.read()
                response_data = json.loads(json_data)

        if response_data is None:
            logger = logging.getLogger()
            try:
                async with self._http_client.get(url) as response:
                    response_data = await response.json(encoding='utf-8')
                    json_data = await response.text()
                    async with aiofiles.open(cache_file_path, 'w', encoding='utf-8') as f:
                        await f.write(json_data)
            except aiohttp.ClientError as e:
                logger.warning('Could not successfully connect to Wikipedia at %s: %s' % (url, e))
            except ValueError as e:
                logger.warning('Could not parse JSON content from Wikipedia at %s: %s' % (url, e))

        if response_data is None:
            try:
                async with aiofiles.open(cache_file_path, encoding='utf-8') as f:
                    json_data = await f.read()
                response_data = json.loads(json_data)
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
        try:
            return Entry(language, name, page_data['title'], page_data['extract'])
        except KeyError as e:
            raise RetrievalError('Could not successfully parse the JSON content returned by %s: %s' % (url, e))


class _Populator:
    def __init__(self, app: App, retriever: _Retriever):
        self._app = app
        self._retriever = retriever

    async def populate(self) -> None:
        locales = set(map(lambda x: x.alias, self._app.configuration.locales))
        await asyncio.gather(*[self._populate_entity(entity, locales) for entity in self._app.ancestry.entities])

    async def _populate_entity(self, entity: Entity, locales: Set[str]) -> None:
        if not isinstance(entity, HasLinks):
            return

        entry_links = set()
        for link in entity.links:
            try:
                entry_language, entry_name = _parse_url(link.url)
                entry_links.add((entry_language, entry_name))
            except NotAnEntryError:
                continue

            entry = None
            if link.label is None:
                with suppress(RetrievalError):
                    entry = await self._retriever.get_entry(entry_language, entry_name)
            await self.populate_link(link, entry_language, entry)

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
                await self.populate_link(added_link, added_entry_language, added_entry)
                entity.links.add(added_link)
                entry_links.add((added_entry_language, added_entry_name))

    async def populate_link(self, link: Link, entry_language: str, entry: Optional[Entry] = None) -> None:
        if link.url.startswith('http:'):
            link.url = 'https:' + link.url[5:]
        if link.media_type is None:
            link.media_type = MediaType('text/html')
        if link.relationship is None:
            link.relationship = 'external'
        if link.locale is None:
            link.locale = entry_language
        if link.description is None:
            # There are valid reasons for links in locales that aren't supported.
            with suppress(ValueError):
                async with self._app.with_locale(link.locale):
                    link.description = _('Read more on Wikipedia.')
        if entry is not None and link.label is None:
            link.label = entry.title


@reactive
class Wikipedia(Extension, Jinja2Provider, PostLoader, GuiBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__retriever = None
        self.__populator = None

    async def post_load(self) -> None:
        await self._populator.populate()

    @reactive
    @property
    def _retriever(self) -> _Retriever:
        if self.__retriever is None:
            self.__retriever = _Retriever(self._app.http_client, self._app.configuration.cache_directory_path / self.name())
        return self.__retriever

    @_retriever.deleter
    def _retriever(self) -> None:
        self.__retriever = None

    @reactive
    @property
    def _populator(self) -> _Populator:
        if self.__populator is None:
            self.__populator = _Populator(self._app, self._retriever)
        return self.__populator

    @_populator.deleter
    def _populator(self) -> None:
        self.__populator = None

    @property
    def filters(self) -> Dict[str, Callable]:
        return {
            'wikipedia': self._filter_wikipedia_links,
        }

    @pass_context
    @sync
    async def _filter_wikipedia_links(self, context: Context, links: Iterable[Link]) -> Iterable[Entry]:
        return filter(
            None,
            await asyncio.gather(*[
                self._filter_wikipedia_link(
                    context.environment.app.locale,
                    link,
                )
                for link
                in links
            ]),
        )

    async def _filter_wikipedia_link(self, locale: str, link: Link) -> Optional[Entry]:
        try:
            entry_language, entry_name = _parse_url(link.url)
        except NotAnEntryError:
            return
        if negotiate_locale(locale, [entry_language]) is None:
            return
        try:
            return await self._retriever.get_entry(entry_language, entry_name)
        except RetrievalError:
            return

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls) -> str:
        return 'Wikipedia'

    @classmethod
    def gui_description(cls) -> str:
        return _("""
Display <a href="https://www.wikipedia.org/">Wikipedia</a> summaries for resources with external links. In your custom <a href="https://jinja2docs.readthedocs.io/en/stable/">Jinja2</a> templates, use the following: <pre><code>
{% with resource=resource_with_links %}
    {% include 'wikipedia.html.j2' %}
{% endwith %}
</code></pre>""")
