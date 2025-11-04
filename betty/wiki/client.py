"""
Interact with the Wikipedia Query API.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, final
from urllib.parse import quote, urlparse

import aiofiles
from geopy import Point

from betty.exception import HumanFacingException
from betty.hashid import hashid
from betty.locale.localizable import Plain
from betty.media_type import MediaType
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, MutableMapping

    from aiohttp import ClientSession

    from betty.user import User


class ClientError(HumanFacingException, RuntimeError):
    """
    A client error.
    """


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


@internal
class Client:
    """
    Fetch information from the Wikipedia Query API.
    """

    def __init__(
        self, *, download_directory_path: Path, http_client: ClientSession, user: User
    ):
        self._download_directory_path = download_directory_path
        self._http_client = http_client
        self._images: MutableMapping[str, Image | None] = {}
        self._user = user

    @contextmanager
    def _catch_json_lookup_errors(self, url: str) -> Iterator[None]:
        try:
            yield
        except (LookupError, TypeError) as error:
            raise ClientError(
                Plain(
                    f"Could not successfully parse the JSON content returned by {url}: {error}"
                )
            ) from error

    async def _fetch_json(self, url: str, *selectors: str | int) -> Any:
        response = await self._http_client.get(url)
        try:
            data = await response.json()
        except JSONDecodeError as error:
            raise ClientError(
                Plain(f"Invalid JSON returned by {url}: {error}")
            ) from error

        with self._catch_json_lookup_errors(url):
            for selector in selectors:
                data = data[selector]
        return data

    async def _get_query_api_data(self, url: str) -> Mapping[str, Any]:
        return cast(
            "Mapping[str, Any]", await self._fetch_json(url, "query", "pages", 0)
        )

    async def _get_page_query_api_data(
        self, page_language: str, page_name: str
    ) -> tuple[str, Mapping[str, Any]]:
        url = f"https://{page_language}.wikipedia.org/w/api.php?action=query&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2&titles={quote(page_name)}"
        return url, await self._get_query_api_data(url)

    async def get_translations(
        self, page_language: str, page_name: str
    ) -> Mapping[str, str]:
        """
        Get the available translations for a page.
        """
        _, api_data = await self._get_page_query_api_data(page_language, page_name)
        try:
            translations_data = api_data["langlinks"]
        except LookupError:
            # There may not be any translations.
            return {}
        return {
            translation_data["lang"]: translation_data["title"]
            for translation_data in translations_data
        }

    async def get_summary(self, page_language: str, page_name: str) -> Summary:
        """
        Get a summary for a page.
        """
        url = f"https://{page_language}.wikipedia.org/api/rest_v1/page/summary/{page_name}"
        api_data = await self._fetch_json(url)
        with self._catch_json_lookup_errors(url):
            title = api_data["titles"]["normalized"]
            extract = (
                api_data["extract_html"]
                if "extract_html" in api_data
                else api_data["extract"]
            )
        return Summary(
            page_language,
            page_name,
            title,
            extract,
        )

    async def get_image(self, page_language: str, page_name: str) -> Image | None:
        """
        Get an image for a page.
        """
        _, api_data = await self._get_page_query_api_data(page_language, page_name)
        try:
            page_image_name = api_data["pageimage"]
        except LookupError:
            # There may not be any images.
            return None

        if page_image_name in self._images:
            return self._images[page_image_name]

        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:{quote(page_image_name)}&iiprop=url|mime|canonicaltitle&format=json&formatversion=2"
        image_info_api_data = await self._get_query_api_data(url)

        with self._catch_json_lookup_errors(url):
            image_info = image_info_api_data["imageinfo"][0]
        image_response = await self._http_client.get(image_info["url"])
        image_path = (
            self._download_directory_path
            / "image"
            / (
                hashid(image_info["url"])
                + Path(urlparse(image_info["url"]).path).suffix.lower()
            )
        )
        image_data = await image_response.read()
        await to_thread(image_path.parent.mkdir, exist_ok=True, parents=True)
        async with aiofiles.open(image_path, mode="wb") as image_f:
            await image_f.write(image_data)
        return Image(
            image_path,
            MediaType(image_info["mime"]),
            # Strip "File:" or any translated equivalent from the beginning of the image's title.
            image_info["canonicaltitle"][image_info["canonicaltitle"].index(":") + 1 :],
            image_info["descriptionurl"],
            Path(urlparse(image_info["url"]).path).name,
        )

    async def get_place_coordinates(
        self, page_language: str, page_name: str
    ) -> Point | None:
        """
        Get the coordinates for a page that is a place.
        """
        url, api_data = await self._get_page_query_api_data(page_language, page_name)
        try:
            coordinates = api_data["coordinates"][0]
        except LookupError:
            # There may not be any coordinates.
            return None
        with self._catch_json_lookup_errors(url):
            if coordinates["globe"] != "earth":
                return None
            latitude = coordinates["lat"]
            longitude = coordinates["lon"]
        return Point(latitude, longitude)
