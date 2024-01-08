from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import mimetypes
import re
from contextlib import suppress
from os.path import getmtime
from pathlib import Path
from time import time
from typing import cast, Any

import aiofiles
import aiohttp
from geopy import Point

from betty.app import App
from betty.asyncio import gather
from betty.functools import filter_suppress
from betty.locale import Localized, negotiate_locale, to_locale, get_data, LocaleNotFoundError, Localey
from betty.media_type import MediaType
from betty.model.ancestry import Link, HasLinks, Place, File, HasFiles


class WikipediaError(BaseException):
    pass


class NotAPageError(WikipediaError, ValueError):
    pass


class RetrievalError(WikipediaError, RuntimeError):
    pass


_URL_PATTERN = re.compile(r'^https?://([a-z]+)\.wikipedia\.org/wiki/([^/?#]+).*$')


def _parse_url(url: str) -> tuple[str, str]:
    match = _URL_PATTERN.fullmatch(url)
    if match is None:
        raise NotAPageError
    return cast(tuple[str, str], match.groups())


class Summary(Localized):
    def __init__(self, locale: str, name: str, title: str, content: str):
        super().__init__(locale=locale)
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


class Image:
    def __init__(
        self,
        path: Path,
        media_type: MediaType,
        title: str,
        wikimedia_commons_url: str,
    ):
        self._path = path
        self._media_type = media_type
        self._title = title
        self._wikimedia_commons_url = wikimedia_commons_url

    @property
    def path(self) -> Path:
        return self._path

    @property
    def media_type(self) -> MediaType:
        return self._media_type

    @property
    def title(self) -> str:
        return self._title

    @property
    def wikimedia_commons_url(self) -> str:
        return self._wikimedia_commons_url


class _Retriever:
    def __init__(
        self,
        http_client: aiohttp.ClientSession,
        cache_directory_path: Path,
        # Default to seven days.
        ttl: int = 86400 * 7,
    ):
        self._cache_directory_path = cache_directory_path
        self._cache_directory_path.mkdir(exist_ok=True, parents=True)
        self._ttl = ttl
        self._http_client = http_client
        self._images: dict[str, Image | None] = {}

    async def _request(self, url: str, extension: str | None = None) -> Any:
        cache_file_path = self._cache_directory_path / hashlib.md5(url.encode("utf-8")).hexdigest()
        if extension:
            cache_file_path = cache_file_path.with_suffix(f'.{extension}')

        response_data = None
        with suppress(FileNotFoundError):
            if getmtime(cache_file_path) + self._ttl > time():
                async with aiofiles.open(cache_file_path, mode='r+b') as f:
                    response_data = await f.read()

        if response_data is None:
            logger = logging.getLogger(__name__)
            try:
                logger.debug(f'Fetching {url}...')
                async with self._http_client.get(url) as response:
                    response_data = await response.read()
                    async with aiofiles.open(cache_file_path, 'w+b') as f:
                        await f.write(response_data)
            except aiohttp.ClientError as error:
                logger.warning(f'Could not successfully connect to Wikipedia at {url}: {error}')
            except asyncio.TimeoutError:
                logger.warning(f'Timeout when connecting to Wikipedia at {url}')

        if response_data is None:
            try:
                async with aiofiles.open(cache_file_path, mode='r+b') as f:
                    response_data = await f.read()
            except FileNotFoundError:
                raise RetrievalError('Could neither fetch %s, nor find an old version in the cache.' % url)

        return response_data

    async def _get_query_api_data(self, url: str) -> dict[str, Any]:
        api_data = json.loads(await self._request(url))
        try:
            return api_data['query']['pages'][0]  # type: ignore[no-any-return]
        except (LookupError, TypeError) as e:
            raise RetrievalError(f'Could not successfully parse the JSON format returned by {url}: {e}')

    async def _get_entry_query_api_data(self, language: str, name: str) -> dict[str, Any]:
        return await self._get_query_api_data(
            f'https://{language}.wikipedia.org/w/api.php?action=query&titles={name}&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2'
        )

    async def get_translations(self, language: str, name: str) -> dict[str, str]:
        api_data = await self._get_entry_query_api_data(language, name)
        try:
            translations_data = api_data['langlinks']
        except KeyError:
            # There may not be any translations.
            return {}
        return {translation_data['lang']: translation_data['title'] for translation_data in translations_data}

    async def get_summary(self, language: str, name: str) -> Summary:
        api_data = json.loads(await self._request(f'https://{language}.wikipedia.org/api/rest_v1/page/summary/{name}'))
        try:
            return Summary(
                language,
                name,
                api_data['titles']['normalized'],
                api_data['extract_html'] if 'extract_html' in api_data else api_data['extract'],
            )
        except KeyError as e:
            raise RetrievalError(f'Could not successfully parse the JSON content: {e}')

    async def get_image(self, language: str, name: str) -> Image | None:
        api_data = await self._get_entry_query_api_data(language, name)
        try:
            page_image_name = api_data['pageimage']
        except KeyError:
            # There may not be any images.
            return None

        if page_image_name in self._images:
            return self._images[page_image_name]

        url = f'https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:{page_image_name}&iiprop=url|mime|canonicaltitle&format=json&formatversion=2'
        image_info_api_data = await self._get_query_api_data(url)

        try:
            image_info = image_info_api_data['imageinfo'][0]
        except KeyError as e:
            raise RetrievalError(f'Could not successfully parse the JSON content returned by {url}: {e}')

        extension = None
        for mimetypes_extension, mimetypes_media_type in mimetypes.types_map.items():
            if mimetypes_media_type == image_info['mime']:
                extension = mimetypes_extension
        await self._request(image_info['url'], extension)

        file_path = (self._cache_directory_path / hashlib.md5(image_info['url'].encode("utf-8")).hexdigest()).with_suffix(f'.{extension}')
        image = Image(
            file_path,
            MediaType(image_info['mime']),
            image_info['canonicaltitle'],
            image_info['descriptionurl'],
        )

        return image

    async def get_place_coordinates(self, language: str, name: str) -> Point | None:
        api_data = await self._get_entry_query_api_data(language, name)
        try:
            coordinates = api_data['coordinates'][0]
        except KeyError:
            # There may not be any coordinates.
            return None
        try:
            if coordinates['globe'] != 'earth':
                return None
            return Point(coordinates['lat'], coordinates['lon'])
        except KeyError as e:
            raise RetrievalError(f'Could not successfully parse the JSON content: {e}')


class _Populator:
    def __init__(self, app: App, retriever: _Retriever):
        self._app = app
        self._retriever = retriever
        self._image_files: dict[Image, File] = {}

    async def populate(self) -> None:
        locales = set(map(lambda x: x.alias, self._app.project.configuration.locales.values()))
        await gather(*(
            self._populate_entity(entity, locales)
            for entity
            in self._app.project.ancestry
            if isinstance(entity, HasLinks)
        ))

    async def _populate_entity(self, entity: HasLinks, locales: set[str]) -> None:
        await self._populate_has_links(entity, locales)

        if isinstance(entity, HasFiles):
            await self._populate_has_files(entity)

        if isinstance(entity, Place):
            await self._populate_place(entity)

    async def _populate_has_links(self, has_links: HasLinks, locales: set[str]) -> None:
        entry_links: set[tuple[str, str]] = set()
        for link in has_links.links:
            try:
                entry_locale, entry_name = _parse_url(link.url)
            except NotAPageError:
                continue
            else:
                try:
                    get_data(entry_locale)
                except LocaleNotFoundError:
                    continue
                else:
                    entry_links.add((entry_locale, entry_name))

            entry = None
            if link.label is None:
                with suppress(RetrievalError):
                    entry = await self._retriever.get_summary(entry_locale, entry_name)
            await self.populate_link(link, entry_locale, entry)

        for entry_locale, entry_name in list(entry_links):
            entry_translations = await self._retriever.get_translations(entry_locale, entry_name)
            if len(entry_translations) == 0:
                continue
            entry_translation_locale_datas: set[Localey] = set(filter_suppress(get_data, LocaleNotFoundError, entry_translations.keys()))
            for locale in locales.difference({entry_locale}):
                added_entry_locale_data = negotiate_locale(locale, entry_translation_locale_datas)
                if added_entry_locale_data is None:
                    continue
                added_entry_locale = to_locale(added_entry_locale_data)
                added_entry_name = entry_translations[added_entry_locale]
                if (added_entry_locale, added_entry_name) in entry_links:
                    continue
                try:
                    added_entry = await self._retriever.get_summary(added_entry_locale, added_entry_name)
                except RetrievalError:
                    continue
                added_link = Link(added_entry.url)
                await self.populate_link(added_link, added_entry_locale, added_entry)
                has_links.links.add(added_link)
                entry_links.add((added_entry_locale, added_entry_name))

    async def populate_link(self, link: Link, entry_locale: str, entry: Summary | None = None) -> None:
        if link.url.startswith('http:'):
            link.url = 'https:' + link.url[5:]
        if link.media_type is None:
            link.media_type = MediaType('text/html')
        if link.relationship is None:
            link.relationship = 'external'
        if link.locale is None:
            link.locale = entry_locale
        if link.description is None:
            # There are valid reasons for links in locales that aren't supported.
            with suppress(ValueError):
                link.description = self._app.localizers.get_negotiated(link.locale)._('Read more on Wikipedia.')
        if entry is not None and link.label is None:
            link.label = entry.title

    async def _populate_place(self, place: Place) -> None:
        await self._populate_place_coordinates(place)

    async def _populate_place_coordinates(self, place: Place) -> None:
        if place.coordinates:
            return

        for link in place.links:
            try:
                entry_locale, entry_name = _parse_url(link.url)
            except NotAPageError:
                continue
            else:
                with suppress(RetrievalError):
                    place.coordinates = await self._retriever.get_place_coordinates(entry_locale, entry_name)
                    return

    async def _populate_has_files(self, has_files: HasFiles & HasLinks) -> None:
        for link in has_files.links:
            try:
                entry_locale, entry_name = _parse_url(link.url)
            except NotAPageError:
                continue
            else:
                with suppress(RetrievalError):
                    image = await self._retriever.get_image(entry_locale, entry_name)
                    if not image:
                        continue

                    try:
                        file = self._image_files[image]
                    except KeyError:
                        file = File(
                            id=f'wikipedia-{image.title}',
                            path=image.path,
                            media_type=image.media_type,
                            links={
                                Link(
                                    f'{image.wikimedia_commons_url}?uselang={locale_configuration.alias}',
                                    label=self._app.localizers[locale_configuration.locale]._('Description, licensing, and image history'),
                                    description=self._app.localizers[locale_configuration.locale]._('Find out more about this image on Wikimedia Commons.'),
                                    locale=locale_configuration.locale,
                                    media_type=MediaType('text/html'),
                                )
                                for locale_configuration
                                in self._app.project.configuration.locales.values()
                            },
                        )
                        self._image_files[image] = file

                    has_files.files.add(file)
                    self._app.project.ancestry.add(file)
                    return
