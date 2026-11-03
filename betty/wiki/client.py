"""
Interact with the Wikipedia Query API.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, final
from urllib.parse import quote, urlsplit

from geopy import Point

from betty.exception import HumanFacingException
from betty.file import write
from betty.hashid import hashid
from betty.localizables.gettext import _
from betty.media_type import resolve_media_type
from betty.operator import Index, Key, Operator

if TYPE_CHECKING:
    from collections.abc import (
        AsyncGenerator,
        Generator,
        Iterable,
        Mapping,
        MutableMapping,
    )

    from aiohttp import ClientResponse, ClientSession
    from ty_extensions import Intersection

    from betty.json import JsonData
    from betty.media_type import MediaType, ResolvableMediaType
    from betty.user.ui import Ui


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

    language: str
    name: str
    title: str
    content: str

    @property
    def url(self) -> str:
        """
        The URL to the web page.
        """
        return f"https://{self.language}.wikipedia.org/wiki/{self.name}"


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


class Client:
    """
    Fetch information from the Wikipedia Query API.
    """

    def __init__(
        self,
        *,
        download_directory: Path,
        http_client: ClientSession,
        media_types: Iterable[ResolvableMediaType] = (),
        ui: Ui,
    ):
        self._download_directory = download_directory
        self._http_client = http_client
        self._images: MutableMapping[str, Image | None] = {}
        self._media_types = {
            str(media_type): media_type
            for media_type in map(resolve_media_type, media_types)
        }
        self._ui = ui

    @contextmanager
    def _human_facing_exception_to_client_error(self) -> Generator[None]:
        try:
            yield
        except HumanFacingException as error:
            raise ClientError(error) from error

    @asynccontextmanager
    async def _get(self, url: str) -> AsyncGenerator[ClientResponse]:
        async with self._http_client.get(url) as response:
            if response.status != 200:
                raise ClientError(
                    _("HTTP {http_status_code} response returned by {url}").format(
                        http_status_code=str(response.status), url=url
                    )
                )
            yield response

    async def _get_json(self, url: str, /) -> dict[str, JsonData]:
        async with self._get(url) as response:
            try:
                return self._lookup_json(dict, await response.json())
            except JSONDecodeError as error:
                raise ClientError(f"Invalid JSON returned by {url}: {error}") from error

    def _lookup_to_operator(self, lookup: int | str, /) -> Operator:
        if isinstance(lookup, int):
            return Index(lookup)
        return Key(lookup)

    def _lookup_json[JsonDataT: None | bool | int | float | str | list | dict](
        self,
        expected: type[JsonDataT] | tuple[type[JsonDataT], ...],
        data: JsonData,
        *lookups: int | str,
    ) -> Intersection[JsonDataT, JsonData]:
        for lookup in lookups:
            try:
                data = data[lookup]  # ty:ignore[invalid-argument-type,not-subscriptable]
            except (LookupError, TypeError) as error:
                raise ClientError(
                    f"Unexpected JSON: cannot get {self._lookup_to_operator(lookup)} from {data!r}"
                ) from error
        if not isinstance(data, expected):
            raise ClientError(
                f"Unexpected JSON: {data!r} was expected to be {expected}"
            )
        return data

    async def _get_query_api_data(self, url: str) -> dict[str, JsonData]:
        data = await self._get_json(url)
        return self._lookup_json(dict, data, "query", "pages", 0)

    async def _get_page_query_api_data(
        self, page_language: str, page_name: str
    ) -> tuple[str, dict[str, JsonData]]:
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
            translations_data = self._lookup_json(list, api_data, "langlinks")
        except ClientError:
            # There may not be any translations.
            return {}
        return {
            self._lookup_json(str, translation_data, "lang"): self._lookup_json(
                str, translation_data, "title"
            )
            for translation_data in translations_data
        }

    async def get_summary(self, page_language: str, page_name: str) -> Summary:
        """
        Get a summary for a page.
        """
        url = f"https://{page_language}.wikipedia.org/api/rest_v1/page/summary/{page_name}"
        api_data = await self._get_json(url)
        title = self._lookup_json(str, api_data, "title")
        extract = (
            self._lookup_json(str, api_data, "extract_html")
            if "extract_html" in api_data
            else self._lookup_json(str, api_data, "extract")
        )
        return Summary(page_language, page_name, title, extract)

    async def get_image(self, page_language: str, page_name: str) -> Image | None:
        """
        Get an image for a page.
        """
        _, api_data = await self._get_page_query_api_data(page_language, page_name)

        # There may not be any images.
        if "pageimage" not in api_data:
            return None

        page_image_name = self._lookup_json(str, api_data, "pageimage")

        if page_image_name in self._images:
            return self._images[page_image_name]

        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:{quote(page_image_name)}&iiprop=url|mime|canonicaltitle&format=json&formatversion=2"
        image_info_api_data = await self._get_query_api_data(url)
        image_info = self._lookup_json(dict, image_info_api_data, "imageinfo", 0)
        image_info_media_type = self._lookup_json(str, image_info, "mime")
        try:
            image_media_type = self._media_types[image_info_media_type]
        except KeyError:
            return None
        image_url = self._lookup_json(str, image_info, "url")
        image_title = self._lookup_json(str, image_info, "canonicaltitle")
        image_wikimedia_commons_url = self._lookup_json(
            str, image_info, "descriptionurl"
        )
        async with self._get(image_url) as image_response:
            image_data = await image_response.read()
        image_path = (
            self._download_directory
            / "image"
            / (hashid(image_url) + Path(urlsplit(image_url).path).suffix.lower())
        )
        await to_thread(image_path.parent.mkdir, exist_ok=True, parents=True)
        await write(image_path, image_data, mode="wb")
        return Image(
            image_path,
            image_media_type,
            # Strip "File:" or any translated equivalent from the beginning of the image's title.
            image_title[image_title.index(":") + 1 :],
            image_wikimedia_commons_url,
            Path(urlsplit(image_url).path).name,
        )

    async def get_place_coordinates(
        self, page_language: str, page_name: str
    ) -> Point | None:
        """
        Get the coordinates for a page that is a place.
        """
        url, api_data = await self._get_page_query_api_data(page_language, page_name)
        try:
            coordinates = self._lookup_json(dict, api_data, "coordinates", 0)
        except ClientError:
            # There may not be any coordinates.
            return None
        globe = self._lookup_json(str, coordinates, "globe")
        if globe != "earth":
            return None
        latitude = self._lookup_json((float, int), coordinates, "lat")
        longitude = self._lookup_json((float, int), coordinates, "lon")
        return Point(latitude, longitude)
