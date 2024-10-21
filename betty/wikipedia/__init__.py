"""
Fetch information from Wikipedia.
"""

from __future__ import annotations

import logging
import re
from asyncio import gather
from collections import defaultdict
from collections.abc import Mapping
from contextlib import suppress, contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import cast, Any, TYPE_CHECKING, final
from urllib.parse import quote, urlparse

from geopy import Point

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.place import Place
from betty.concurrent import Lock, AsynchronizedLock, RateLimiter
from betty.fetch import FetchError
from betty.functools import filter_suppress
from betty.locale import (
    negotiate_locale,
    to_locale,
    get_data,
    Localey,
    UNDETERMINED_LOCALE,
)
from betty.locale.error import LocaleError
from betty.locale.localizable import plain
from betty.media_type import MediaType
from betty.media_type.media_types import HTML

if TYPE_CHECKING:
    from betty.wikipedia.copyright_notice import WikipediaContributors
    from betty.ancestry import Ancestry
    from betty.locale.localizer import LocalizerRepository
    from betty.fetch import Fetcher
    from collections.abc import Sequence, MutableSequence, MutableMapping, Iterator


class NotAPageError(ValueError):
    """
    Raised when a URL does not point to a Wikipedia page.
    """

    pass  # pragma: no cover


_URL_PATTERN = re.compile(r"^https?://([a-z]+)\.wikipedia\.org/wiki/([^/?#]+).*$")


def _parse_url(url: str) -> tuple[str, str]:
    match = _URL_PATTERN.fullmatch(url)
    if match is None:
        raise NotAPageError
    return cast(tuple[str, str], match.groups())


@final
@dataclass(frozen=True)
class Summary:
    """
    A Wikipedia page summary.
    """

    locale: str
    name: str
    title: str
    content: str

    @property
    def url(self) -> str:
        """
        The URL to the web page.
        """
        return f"https://{self.locale}.wikipedia.org/wiki/{self.name}"


@final
@dataclass(frozen=True)
class Image:
    """
    An image from Wikimedia Commons.
    """

    path: Path
    media_type: MediaType
    title: str
    wikimedia_commons_url: str
    name: str


class _Retriever:
    _WIKIPEDIA_RATE_LIMIT = 200

    def __init__(
        self,
        fetcher: Fetcher,
    ):
        self._fetcher = fetcher
        self._images: MutableMapping[str, Image | None] = {}
        self._rate_limiter = RateLimiter(self._WIKIPEDIA_RATE_LIMIT)

    @contextmanager
    def _catch_exceptions(self) -> Iterator[None]:
        try:
            yield
        except FetchError as error:
            logging.getLogger(__name__).warning(str(error))

    async def _fetch_json(self, url: str, *selectors: str | int) -> Any:
        async with self._rate_limiter:
            response = await self._fetcher.fetch(url)
        try:
            data = response.json
        except JSONDecodeError as error:
            raise FetchError(
                plain(f"Invalid JSON returned by {url}: {error}")
            ) from error

        try:
            for selector in selectors:
                data = data[selector]
        except (LookupError, TypeError) as error:
            raise FetchError(
                plain(
                    f"Could not successfully parse the JSON format returned by {url}: {error}"
                )
            ) from error
        return data

    async def _get_query_api_data(self, url: str) -> Mapping[str, Any]:
        return cast(Mapping[str, Any], await self._fetch_json(url, "query", "pages", 0))

    async def _get_page_query_api_data(
        self, page_language: str, page_name: str
    ) -> Mapping[str, Any]:
        return await self._get_query_api_data(
            f"https://{page_language}.wikipedia.org/w/api.php?action=query&titles={quote(page_name)}&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        )

    async def get_translations(
        self, page_language: str, page_name: str
    ) -> Mapping[str, str]:
        try:
            api_data = await self._get_page_query_api_data(page_language, page_name)
        except FetchError as error:
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
        with self._catch_exceptions():
            url = f"https://{page_language}.wikipedia.org/api/rest_v1/page/summary/{page_name}"
            api_data = await self._fetch_json(url)
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
                raise FetchError(
                    plain(
                        f"Could not successfully parse the JSON content returned by {url}: {error}"
                    )
                ) from error

    async def get_image(self, page_language: str, page_name: str) -> Image | None:
        with self._catch_exceptions():
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
                raise FetchError(
                    plain(
                        f"Could not successfully parse the JSON content returned by {url}: {error}"
                    )
                ) from error
            async with self._rate_limiter:
                image_path = await self._fetcher.fetch_file(image_info["url"])
            image = Image(
                image_path,
                MediaType(image_info["mime"]),
                # Strip "File:" or any translated equivalent from the beginning of the image's title.
                image_info["canonicaltitle"][
                    image_info["canonicaltitle"].index(":") + 1 :
                ],
                image_info["descriptionurl"],
                Path(urlparse(image_info["url"]).path).name,
            )

            return image

    async def get_place_coordinates(
        self, page_language: str, page_name: str
    ) -> Point | None:
        with self._catch_exceptions():
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
                raise FetchError(
                    plain(f"Could not successfully parse the JSON content: {error}")
                ) from error


class _Populator:
    def __init__(
        self,
        ancestry: Ancestry,
        locales: Sequence[str],
        localizers: LocalizerRepository,
        retriever: _Retriever,
        copyright_notice: WikipediaContributors,
    ):
        self._ancestry = ancestry
        self._locales = locales
        self._localizers = localizers
        self._retriever = retriever
        self._image_files: MutableMapping[Image, File] = {}
        self._image_files_locks: Mapping[Image, Lock] = defaultdict(
            AsynchronizedLock.threading
        )
        self._copyright_notice = copyright_notice

    async def populate(self) -> None:
        await gather(
            *(
                self._populate_entity(entity, self._locales)
                for entity in self._ancestry
                if isinstance(entity, HasLinks)
            )
        )

    async def _populate_entity(self, entity: HasLinks, locales: Sequence[str]) -> None:
        populations = [self._populate_has_links(entity, locales)]
        if isinstance(entity, HasFileReferences):
            populations.append(self._populate_has_file_references(entity))
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
                except LocaleError:
                    continue
                else:
                    summary_links.append((page_language, page_name))

            summary = None
            if not link.label:
                with suppress(FetchError):
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
                filter_suppress(get_data, LocaleError, page_translations.keys())
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
            link.media_type = HTML
        if link.relationship is None:
            link.relationship = "external"
        if link.locale is UNDETERMINED_LOCALE:
            link.locale = summary_language
        if not link.description:
            # There are valid reasons for links in locales that aren't supported.
            with suppress(ValueError):
                link.description = (
                    await self._localizers.get_negotiated(link.locale)
                )._("Read more on Wikipedia.")
        if summary is not None and not link.label:
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

    async def _populate_has_file_references(
        self, has_file_references: HasFileReferences & HasLinks
    ) -> None:
        await gather(
            *(
                self._populate_has_file_references_link(has_file_references, link)
                for link in has_file_references.links
            )
        )

    async def _populate_has_file_references_link(
        self, has_file_references: HasFileReferences & HasLinks, link: Link
    ) -> None:
        try:
            page_language, page_name = _parse_url(link.url)
        except NotAPageError:
            return
        else:
            image = await self._retriever.get_image(page_language, page_name)
            if not image:
                return
            await self._image_file_reference(has_file_references, image)

    async def _image_file_reference(
        self, has_file_references: HasFileReferences, image: Image
    ) -> FileReference:
        async with self._image_files_locks[image]:
            try:
                file = self._image_files[image]
            except KeyError:
                links = []
                for locale in self._locales:
                    localizer = await self._localizers.get(locale)
                    links.append(
                        Link(
                            f"{image.wikimedia_commons_url}?uselang={locale}",
                            label=localizer._(
                                "Description, licensing, and image history"
                            ),
                            description=localizer._(
                                "Find out more about this image on Wikimedia Commons."
                            ),
                            locale=locale,
                            media_type=HTML,
                        )
                    )
                file = File(
                    id=f"wikipedia-{image.title}",
                    name=image.name,
                    path=image.path,
                    media_type=image.media_type,
                    links=links,
                    copyright_notice=self._copyright_notice,
                )
                self._image_files[image] = file
                self._ancestry.add(file)
            file_reference = FileReference(has_file_references, file)
            self._ancestry.add(file_reference)
            return file_reference
