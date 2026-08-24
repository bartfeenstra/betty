"""
Interact with the Wikipedia Query API.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Any, final
from urllib.parse import quote, urlsplit

from geopy import Point

from betty.assertions.float import assert_float
from betty.assertions.mapping import assert_mapping
from betty.assertions.str import assert_str
from betty.exception import HumanFacingException, reraise_with_indicator
from betty.file import write
from betty.hashid import hashid
from betty.indicator import Url
from betty.indicator.operator import Index, Key, OperatorError, Operators
from betty.localizables.gettext import _
from betty.media_type import MediaType

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, Mapping, MutableMapping

    from aiohttp import ClientResponse, ClientSession

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
        self, *, download_directory: Path, http_client: ClientSession, user: User
    ):
        self._download_directory = download_directory
        self._http_client = http_client
        self._images: MutableMapping[str, Image | None] = {}
        self._user = user

    @contextmanager
    def _human_facing_exception_to_client_error(self) -> Iterator[None]:
        try:
            yield
        except HumanFacingException as error:
            raise ClientError(error) from error
        except OperatorError as error:
            raise ClientError(str(error)) from error

    @asynccontextmanager
    async def _get(self, url: str) -> AsyncIterator[ClientResponse]:
        async with self._http_client.get(url) as response:
            if response.status != 200:
                raise ClientError(
                    _("HTTP {http_status_code} response returned by {url}").format(
                        http_status_code=str(response.status), url=url
                    )
                )
            yield response

    async def _get_json(self, url: str) -> Any:
        async with self._get(url) as response:
            try:
                return await response.json()
            except JSONDecodeError as error:
                raise ClientError(f"Invalid JSON returned by {url}: {error}") from error

    async def _get_query_api_data(self, url: str) -> Mapping[str, Any]:
        data = await self._get_json(url)
        with (
            self._human_facing_exception_to_client_error(),
            reraise_with_indicator(Url(url)),
        ):
            return Operators(Key("query"), Key("pages"), Index(0)).get(
                data, assert_mapping(None, assert_str())
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

        with (
            self._human_facing_exception_to_client_error(),
            reraise_with_indicator(Url(url)),
        ):
            api_data = await self._get_json(url)

            title = Operators(Key("titles"), Key("normalized")).get(
                api_data, assert_str()
            )
            extract = Operators(
                Key("extract_html") if "extract_html" in api_data else Key("extract")
            ).get(api_data, assert_str())
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

        image_info_selectors = (Key("imageinfo"), Index(0))
        with (
            self._human_facing_exception_to_client_error(),
            reraise_with_indicator(Url(url)),
        ):
            image_info = Operators(*image_info_selectors).get(
                image_info_api_data, assert_mapping()
            )
            with reraise_with_indicator(*image_info_selectors):
                image_url = Key("url").get(image_info, assert_str())
                image_media_type = Key("mime").get(image_info, MediaType)
                image_title = Key("canonicaltitle").get(image_info, assert_str())
                image_wikimedia_commons_url = Key("descriptionurl").get(
                    image_info, assert_str()
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
            image_title[image_title.build(":") + 1 :],
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
            coordinates = api_data["coordinates"][0]
        except LookupError:
            # There may not be any coordinates.
            return None

        with (
            self._human_facing_exception_to_client_error(),
            reraise_with_indicator(Url(url)),
        ):
            globe = Key("globe").get(coordinates, assert_str())
            if globe != "earth":
                return None
            latitude = Key("lat").get(coordinates, assert_float())
            longitude = Key("lon").get(coordinates, assert_float())
        return Point(latitude, longitude)
