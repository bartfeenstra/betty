"""
Interact with the Wikipedia Query API.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, final
from urllib.parse import quote, urlparse

from geopy import Point

from betty.fetch import Fetcher, FetchError
from betty.locale.localizable import plain
from betty.media_type import MediaType
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, MutableMapping

    from betty.concurrent import RateLimiter


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


RATE_LIMIT = 200


@internal
class Client:
    """
    Fetch information from the Wikipedia Query API.
    """

    def __init__(self, fetcher: Fetcher, rate_limiter: RateLimiter):
        self._fetcher = fetcher
        self._images: MutableMapping[str, Image | None] = {}
        self._rate_limiter = rate_limiter

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
        return cast(
            "Mapping[str, Any]", await self._fetch_json(url, "query", "pages", 0)
        )

    async def _get_page_query_api_data(
        self, page_language: str, page_name: str
    ) -> Mapping[str, Any]:
        return await self._get_query_api_data(
            f"https://{page_language}.wikipedia.org/w/api.php?action=query&titles={quote(page_name)}&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        )

    async def get_translations(
        self, page_language: str, page_name: str
    ) -> Mapping[str, str]:
        """
        Get the available translations for a page.
        """
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
        """
        Get a summary for a page.
        """
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
        """
        Get an image for a page.
        """
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
            return Image(
                image_path,
                MediaType(image_info["mime"]),
                # Strip "File:" or any translated equivalent from the beginning of the image's title.
                image_info["canonicaltitle"][
                    image_info["canonicaltitle"].index(":") + 1 :
                ],
                image_info["descriptionurl"],
                Path(urlparse(image_info["url"]).path).name,
            )

    async def get_place_coordinates(
        self, page_language: str, page_name: str
    ) -> Point | None:
        """
        Get the coordinates for a page that is a place.
        """
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
