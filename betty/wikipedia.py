"""
Fetch information from Wikipedia.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import defaultdict
from contextlib import suppress
from time import time
from typing import cast, Any, TYPE_CHECKING
from urllib.parse import quote

import aiohttp
from aiohttp import ClientResponse
from geopy import Point

from betty.asyncio import gather
from betty.concurrent import RateLimiter, _Lock, AsynchronizedLock
from betty.functools import filter_suppress
from betty.hashid import hashid
from betty.locale import (
    Localized,
    negotiate_locale,
    to_locale,
    get_data,
    LocaleNotFoundError,
    Localey,
)
from betty.media_type import MediaType
from betty.model.ancestry import Link, HasLinks, Place, File, HasFiles

if TYPE_CHECKING:
    from betty.app import App
    from betty.cache.file import BinaryFileCache
    from betty.cache import Cache, CacheItemValueT
    from pathlib import Path
    from collections.abc import (
        Sequence,
        MutableSequence,
        Callable,
        Awaitable,
        Mapping,
        MutableMapping,
    )


class WikipediaError(BaseException):
    """
    An error raised by Betty's Wikipedia API.
    """

    pass  # pragma: no cover


class NotAPageError(WikipediaError, ValueError):
    """
    Raised when a URL does not point to a Wikipedia page.
    """

    pass  # pragma: no cover


class RetrievalError(WikipediaError, RuntimeError):
    """
    An error that occurred when retrieving content from Wikipedia.
    """

    pass  # pragma: no cover


_URL_PATTERN = re.compile(r"^https?://([a-z]+)\.wikipedia\.org/wiki/([^/?#]+).*$")


def _parse_url(url: str) -> tuple[str, str]:
    match = _URL_PATTERN.fullmatch(url)
    if match is None:
        raise NotAPageError
    return cast(tuple[str, str], match.groups())


class Summary(Localized):
    """
    A Wikipedia page summary.
    """

    def __init__(self, locale: str, name: str, title: str, content: str):
        super().__init__(locale=locale)
        self._name = name
        self._title = title
        self._content = content

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Summary):
            return False
        if self.name != other.name:
            return False
        if self.url != other.url:
            return False
        if self.title != other.title:
            return False
        if self.content != other.content:
            return False
        return True

    @property
    def name(self) -> str:
        """
        The page's machine name.
        """
        return self._name

    @property
    def url(self) -> str:
        """
        The URL to the web page.
        """
        return "https://%s.wikipedia.org/wiki/%s" % (self.locale, self._name)

    @property
    def title(self) -> str:
        """
        The page's human-readable title.
        """
        return self._title

    @property
    def content(self) -> str:
        """
        The page's human-readable summary content.
        """
        return self._content


class Image:
    """
    An image from Wikimedia Commons.
    """

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

    def __hash__(self) -> int:
        return hash(
            (self.path, self.media_type, self.title, self.wikimedia_commons_url)
        )

    @property
    def path(self) -> Path:
        """
        The path to the image on disk.
        """
        return self._path

    @property
    def media_type(self) -> MediaType:
        """
        The image's media type.
        """
        return self._media_type

    @property
    def title(self) -> str:
        """
        The human-readable image title.
        """
        return self._title

    @property
    def wikimedia_commons_url(self) -> str:
        """
        The URL to the Wikimedia Commons web page for this image.
        """
        return self._wikimedia_commons_url


class _Fetcher:
    _WIKIPEDIA_RATE_LIMIT = 200

    def __init__(
        self,
        http_client: aiohttp.ClientSession,
        cache: Cache[str],
        binary_file_cache: BinaryFileCache,
        # Default to seven days.
        ttl: int = 86400 * 7,
    ):
        self._cache = cache
        self._binary_file_cache = binary_file_cache
        self._ttl = ttl
        self._http_client = http_client
        self._rate_limiter = RateLimiter(self._WIKIPEDIA_RATE_LIMIT)
        self._images: dict[str, Image | None] = {}
        self._logger = logging.getLogger(__name__)

    async def _fetch(
        self,
        url: str,
        cache: Cache[CacheItemValueT],
        response_mapper: Callable[[ClientResponse], Awaitable[CacheItemValueT]],
    ) -> tuple[CacheItemValueT, str]:
        cache_item_id = hashid(url)

        response_data: CacheItemValueT | None = None
        async with cache.getset(cache_item_id) as (cache_item, setter):
            if cache_item and cache_item.modified + self._ttl > time():
                response_data = await cache_item.value()
            else:
                async with self._rate_limiter:
                    self._logger.debug(f"Fetching {url}...")
                    try:
                        async with self._http_client.get(url) as response:
                            response_data = await response_mapper(response)
                    except aiohttp.ClientError as error:
                        self._logger.warning(
                            f"Could not successfully connect to {url}: {error}"
                        )
                    except asyncio.TimeoutError:
                        self._logger.warning(f"Timeout when connecting to {url}")
                    else:
                        await setter(response_data)

        if response_data is None:
            if cache_item:
                response_data = await cache_item.value()
            else:
                raise RetrievalError(
                    f"Could neither fetch {url}, nor find an old version in the cache."
                )

        return response_data, cache_item_id

    async def fetch(self, url: str) -> str:
        response_data, _ = await self._fetch(url, self._cache, ClientResponse.text)
        return response_data

    async def fetch_file(self, url: str) -> Path:
        _, cache_item_id = await self._fetch(
            url, self._binary_file_cache, ClientResponse.read
        )
        return self._binary_file_cache.cache_item_file_path(cache_item_id)


class _Retriever:
    def __init__(
        self,
        fetcher: _Fetcher,
    ):
        self._fetcher = fetcher
        self._images: dict[str, Image | None] = {}

    async def _get_query_api_data(self, url: str) -> dict[str, Any]:
        response_data = await self._fetcher.fetch(url)
        api_data = json.loads(response_data)
        try:
            return api_data["query"]["pages"][0]  # type: ignore[no-any-return]
        except (LookupError, TypeError) as error:
            raise RetrievalError(
                f"Could not successfully parse the JSON format returned by {url}: {error}"
            ) from error

    async def _get_page_query_api_data(
        self, page_language: str, page_name: str
    ) -> dict[str, Any]:
        return await self._get_query_api_data(
            f"https://{page_language}.wikipedia.org/w/api.php?action=query&titles={quote(page_name)}&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        )

    async def get_translations(
        self, page_language: str, page_name: str
    ) -> dict[str, str]:
        try:
            api_data = await self._get_page_query_api_data(page_language, page_name)
        except RetrievalError as error:
            logger = logging.getLogger(__name__)
            logger.warning(str(error))
            return {}
        try:
            translations_data = api_data["langlinks"]
        except LookupError:
            # There may not be any translations.
            return {}
        return {
            translation_data["lang"]: translation_data["title"]
            for translation_data in translations_data
        }

    async def get_summary(self, page_language: str, page_name: str) -> Summary | None:
        try:
            url = f"https://{page_language}.wikipedia.org/api/rest_v1/page/summary/{page_name}"
            response_data = await self._fetcher.fetch(url)
            try:
                api_data = json.loads(response_data)
            except json.JSONDecodeError as error:
                raise RetrievalError(
                    f"Could not successfully parse the JSON content returned by {url}: {error}"
                ) from error
            else:
                try:
                    return Summary(
                        page_language,
                        page_name,
                        api_data["titles"]["normalized"],
                        (
                            api_data["extract_html"]
                            if "extract_html" in api_data
                            else api_data["extract"]
                        ),
                    )
                except LookupError as error:
                    raise RetrievalError(
                        f"Could not successfully parse the JSON content returned by {url}: {error}"
                    ) from error
        except RetrievalError as error:
            logger = logging.getLogger(__name__)
            logger.warning(str(error))
            return None

    async def get_image(self, page_language: str, page_name: str) -> Image | None:
        try:
            api_data = await self._get_page_query_api_data(page_language, page_name)
            try:
                page_image_name = api_data["pageimage"]
            except LookupError:
                # There may not be any images.
                return None

            if page_image_name in self._images:
                return self._images[page_image_name]

            url = f"https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:{quote(page_image_name)}&iiprop=url|mime|canonicaltitle&format=json&formatversion=2"
            image_info_api_data = await self._get_query_api_data(url)

            try:
                image_info = image_info_api_data["imageinfo"][0]
            except LookupError as error:
                raise RetrievalError(
                    f"Could not successfully parse the JSON content returned by {url}: {error}"
                ) from error
            image = Image(
                await self._fetcher.fetch_file(image_info["url"]),
                MediaType(image_info["mime"]),
                # Strip "File:" or any translated equivalent from the beginning of the image's title.
                image_info["canonicaltitle"][
                    image_info["canonicaltitle"].index(":") + 1 :
                ],
                image_info["descriptionurl"],
            )

            return image
        except RetrievalError as error:
            logger = logging.getLogger(__name__)
            logger.warning(str(error))
            return None

    async def get_place_coordinates(
        self, page_language: str, page_name: str
    ) -> Point | None:
        try:
            api_data = await self._get_page_query_api_data(page_language, page_name)
            try:
                coordinates = api_data["coordinates"][0]
            except LookupError:
                # There may not be any coordinates.
                return None
            try:
                if coordinates["globe"] != "earth":
                    return None
                return Point(coordinates["lat"], coordinates["lon"])
            except LookupError as error:
                raise RetrievalError(
                    f"Could not successfully parse the JSON content: {error}"
                ) from error
        except RetrievalError as error:
            logger = logging.getLogger(__name__)
            logger.warning(str(error))
            return None


class _Populator:
    def __init__(self, app: App, retriever: _Retriever):
        self._app = app
        self._retriever = retriever
        self._image_files: MutableMapping[Image, File] = {}
        self._image_files_locks: Mapping[Image, _Lock] = defaultdict(
            AsynchronizedLock.threading
        )

    async def populate(self) -> None:
        locales = [x.alias for x in self._app.project.configuration.locales.values()]
        await gather(
            *(
                self._populate_entity(entity, locales)
                for entity in self._app.project.ancestry
                if isinstance(entity, HasLinks)
            )
        )

    async def _populate_entity(self, entity: HasLinks, locales: Sequence[str]) -> None:
        populations = [self._populate_has_links(entity, locales)]
        if isinstance(entity, HasFiles):
            populations.append(self._populate_has_files(entity))
        if isinstance(entity, Place):
            populations.append(self._populate_place(entity))
        await gather(*populations)

    async def _populate_has_links(
        self, has_links: HasLinks, locales: Sequence[str]
    ) -> None:
        summary_links: MutableSequence[tuple[str, str]] = []
        for link in has_links.links:
            try:
                page_language, page_name = _parse_url(link.url)
            except NotAPageError:
                continue
            else:
                try:
                    get_data(page_language)
                except LocaleNotFoundError:
                    continue
                else:
                    summary_links.append((page_language, page_name))

            summary = None
            if link.label is None:
                with suppress(RetrievalError):
                    summary = await self._retriever.get_summary(
                        page_language, page_name
                    )
            await self.populate_link(link, page_language, summary)
        await self._populate_has_links_with_translation(
            has_links, locales, summary_links
        )

    async def _populate_has_links_with_translation(
        self,
        has_links: HasLinks,
        locales: Sequence[str],
        summary_links: MutableSequence[tuple[str, str]],
    ) -> None:
        for page_language, page_name in summary_links:
            page_translations = await self._retriever.get_translations(
                page_language, page_name
            )
            if len(page_translations) == 0:
                continue
            page_translation_locale_datas: Sequence[Localey] = list(
                filter_suppress(get_data, LocaleNotFoundError, page_translations.keys())
            )
            for locale in locales:
                if locale == page_language:
                    continue
                added_page_locale_data = negotiate_locale(
                    locale, page_translation_locale_datas
                )
                if added_page_locale_data is None:
                    continue
                added_page_language = to_locale(added_page_locale_data)
                added_page_name = page_translations[added_page_language]
                if (added_page_language, added_page_name) in summary_links:
                    continue
                added_summary = await self._retriever.get_summary(
                    added_page_language, added_page_name
                )
                if not added_summary:
                    continue
                added_link = Link(added_summary.url)
                await self.populate_link(added_link, added_page_language, added_summary)
                has_links.links.append(added_link)
                summary_links.append((added_page_language, added_page_name))
            return

    async def populate_link(
        self, link: Link, summary_language: str, summary: Summary | None = None
    ) -> None:
        if link.url.startswith("http:"):
            link.url = "https:" + link.url[5:]
        if link.media_type is None:
            link.media_type = MediaType("text/html")
        if link.relationship is None:
            link.relationship = "external"
        if link.locale is None:
            link.locale = summary_language
        if link.description is None:
            # There are valid reasons for links in locales that aren't supported.
            with suppress(ValueError):
                link.description = (
                    await self._app.localizers.get_negotiated(link.locale)
                )._("Read more on Wikipedia.")
        if summary is not None and link.label is None:
            link.label = summary.title

    async def _populate_place(self, place: Place) -> None:
        await self._populate_place_coordinates(place)

    async def _populate_place_coordinates(self, place: Place) -> None:
        await gather(
            *(
                self._populate_place_coordinates_link(place, link)
                for link in place.links
            )
        )

    async def _populate_place_coordinates_link(self, place: Place, link: Link) -> None:
        try:
            page_language, page_name = _parse_url(link.url)
        except NotAPageError:
            return
        else:
            coordinates = await self._retriever.get_place_coordinates(
                page_language, page_name
            )
            if coordinates:
                place.coordinates = coordinates

    async def _populate_has_files(self, has_files: HasFiles & HasLinks) -> None:
        await gather(
            *(
                self._populate_has_files_link(has_files, link)
                for link in has_files.links
            )
        )

    async def _populate_has_files_link(
        self, has_files: HasFiles & HasLinks, link: Link
    ) -> None:
        try:
            page_language, page_name = _parse_url(link.url)
        except NotAPageError:
            return
        else:
            image = await self._retriever.get_image(page_language, page_name)
            if not image:
                return
            has_files.files.add(await self._image_file(image))

    async def _image_file(self, image: Image) -> File:
        async with self._image_files_locks[image]:
            try:
                return self._image_files[image]
            except KeyError:
                links = []
                for (
                    locale_configuration
                ) in self._app.project.configuration.locales.values():
                    localizer = await self._app.localizers.get(
                        locale_configuration.locale
                    )
                    links.append(
                        Link(
                            f"{image.wikimedia_commons_url}?uselang={locale_configuration.alias}",
                            label=localizer._(
                                "Description, licensing, and image history"
                            ),
                            description=localizer._(
                                "Find out more about this image on Wikimedia Commons."
                            ),
                            locale=locale_configuration.locale,
                            media_type=MediaType("text/html"),
                        )
                    )
                file = File(
                    id=f"wikipedia-{image.title}",
                    path=image.path,
                    media_type=image.media_type,
                    links=links,
                )
                self._image_files[image] = file
                self._app.project.ancestry.add(file)
                return file
