from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

import aiofiles
import pytest
from aiohttp import ClientSession
from geopy import Point

from betty.media_type.media_types import SVG
from betty.test_utils.user import StaticUser
from betty.wiki.client import Client, ClientError, Summary

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from aioresponses import aioresponses
    from pytest_mock import MockerFixture


class TestSummary:
    async def test_url(self) -> None:
        sut = Summary(
            "nl",
            "Amsterdam",
            "Title for Amsterdam",
            "Content for Amsterdam",
        )
        assert sut.url == "https://nl.wikipedia.org/wiki/Amsterdam"


class TestClient:
    @pytest.mark.parametrize(
        "response_body",
        [
            "{Haha Im not rly JSON}",
            b"{Haha Im not rly JSON}",
            dumps({}),
            dumps({"query": {}}),
            dumps({"query": {"pages": {}}}),
            dumps({"query": {"pages": []}}),
        ],
    )
    async def test_get_translations__should_error(
        self,
        response_body: str,
        http_client_mock: aioresponses,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = f"https://{page_language}.wikipedia.org/w/api.php?action=query&titles={quote(page_name)}&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=response_body)
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            with pytest.raises(ClientError):
                await sut.get_translations(page_language, page_name)

    @pytest.mark.parametrize(
        ("expected", "response_body"),
        [
            (
                {},
                {
                    "query": {
                        "pages": [{}],
                    },
                },
            ),
            (
                {
                    "nl": "Amsterdam",
                    "uk": "Амстердам",
                },
                {
                    "query": {
                        "pages": [
                            {
                                "langlinks": [
                                    {
                                        "lang": "nl",
                                        "title": "Amsterdam",
                                    },
                                    {
                                        "lang": "uk",
                                        "title": "Амстердам",
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
        ],
    )
    async def test_get_translations__should_return(
        self,
        expected: Mapping[str, str],
        response_body: Mapping[str, Any],
        http_client_mock: aioresponses,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"

        download_directory_path = tmp_path / "download"
        http_client_mock.get(url, body=dumps(response_body))
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            translations = await sut.get_translations(page_language, page_name)
        assert expected == translations

    @pytest.mark.parametrize(
        ("expected", "page_response_json"),
        [
            (
                None,
                {},
            ),
            (
                None,
                {
                    "titles": {},
                },
            ),
            (
                None,
                {
                    "titles": {},
                    "extract": "De hoofdstad van Nederland.",
                },
            ),
            (
                None,
                {
                    "extract": "De hoofdstad van Nederland.",
                },
            ),
        ],
    )
    async def test_get_summary__should_error(
        self,
        expected: Summary | None,
        page_response_json: Mapping[str, Any],
        http_client_mock: aioresponses,
        tmp_path: Path,
    ) -> None:
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam & Omstreken"
        )

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=dumps(page_response_json))
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            with pytest.raises(ClientError):
                await sut.get_summary(page_language, page_name)

    @pytest.mark.parametrize(
        ("expected", "page_response_json"),
        [
            (
                Summary(
                    "en",
                    "Amsterdam & Omstreken",
                    "Amstelredam",
                    "De hoofdstad van Nederland.",
                ),
                {
                    "titles": {
                        "normalized": "Amstelredam",
                    },
                    "extract": "De hoofdstad van Nederland.",
                },
            ),
            (
                Summary(
                    "en",
                    "Amsterdam & Omstreken",
                    "Amstelredam",
                    "De hoofdstad van Nederland.",
                ),
                {
                    "titles": {
                        "normalized": "Amstelredam",
                    },
                    "extract_html": "De hoofdstad van Nederland.",
                },
            ),
        ],
    )
    async def test_get_summary__should_return(
        self,
        expected: Summary,
        page_response_json: Mapping[str, Any],
        http_client_mock: aioresponses,
        tmp_path: Path,
    ) -> None:
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam & Omstreken"
        )

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=dumps(page_response_json))
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            actual = await sut.get_summary(page_language, page_name)
        assert actual == expected

    @pytest.mark.parametrize(
        "page_response_json",
        [
            ({},),
            (
                {
                    "query": {},
                },
            ),
            (
                {
                    "query": {
                        "pages": [],
                    },
                },
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "coordinates": [
                                    {
                                        "lon": 6.66666667,
                                        "globe": "earth",
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "coordinates": [
                                    {
                                        "lat": 52.35,
                                        "globe": "earth",
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "coordinates": [
                                    {
                                        "lat": 52.35,
                                        "lon": 6.66666667,
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
        ],
    )
    async def test_get_place_coordinates__should_error(
        self,
        page_response_json: Mapping[str, Any],
        http_client_mock: aioresponses,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=dumps(page_response_json))
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            with pytest.raises(ClientError):
                await sut.get_place_coordinates(page_language, page_name)

    @pytest.mark.parametrize(
        ("expected", "page_response_json"),
        [
            (
                None,
                {
                    "query": {
                        "pages": [{}],
                    },
                },
            ),
            (
                None,
                {
                    "query": {
                        "pages": [
                            {
                                "coordinates": [],
                            }
                        ],
                    },
                },
            ),
            # Almelo.
            (
                Point(52.35, 6.66666667),
                {
                    "query": {
                        "pages": [
                            {
                                "coordinates": [
                                    {
                                        "lat": 52.35,
                                        "lon": 6.66666667,
                                        "globe": "earth",
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
            # Tranquility Base.
            (
                None,
                {
                    "query": {
                        "pages": [
                            {
                                "coordinates": [
                                    {
                                        "lat": 0.6875,
                                        "lon": 23.43333333,
                                        "globe": "moon",
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
        ],
    )
    async def test_get_place_coordinates__should_return(
        self,
        expected: Point | None,
        page_response_json: Mapping[str, Any],
        http_client_mock: aioresponses,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=dumps(page_response_json))
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            actual = await sut.get_place_coordinates(page_language, page_name)
        assert actual == expected

    @pytest.mark.parametrize(
        ("page_response_json", "file_response_json"),
        [
            (
                {},
                None,
            ),
            (
                {"query": {}},
                None,
            ),
            (
                {"query": {"pages": []}},
                None,
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "pageimage": "Amsterdam & Omstreken",
                            },
                        ]
                    }
                },
                {},
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "pageimage": "Amsterdam & Omstreken",
                            },
                        ]
                    }
                },
                {"query": {}},
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "pageimage": "Amsterdam & Omstreken",
                            },
                        ]
                    }
                },
                {"query": {"pages": []}},
            ),
            (
                {
                    "query": {
                        "pages": [
                            {
                                "pageimage": "Amsterdam & Omstreken",
                            },
                        ]
                    }
                },
                {
                    "query": {
                        "pages": [
                            {
                                "imageinfo": [],
                            },
                        ]
                    }
                },
            ),
        ],
    )
    async def test_get_image__should_error(
        self,
        page_response_json: Mapping[str, Any],
        file_response_json: Mapping[str, Any] | None,
        http_client_mock: aioresponses,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")

        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        file_url = "https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:Amsterdam%20%26%20Omstreken&iiprop=url|mime|canonicaltitle&format=json&formatversion=2"
        image_url = "https://example.com/image.svg"
        image_data = bytes(123)

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=dumps(page_response_json))
        http_client_mock.get(file_url, body=dumps(file_response_json))
        http_client_mock.get(image_url, body=image_data)
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            with pytest.raises(ClientError):
                await sut.get_image(page_language, page_name)

    @pytest.mark.parametrize(
        ("expected", "page_response_json", "file_response_json"),
        [
            # A successful response.
            (
                True,
                {
                    "query": {
                        "pages": [
                            {
                                "pageimage": "Amsterdam & Omstreken",
                            }
                        ],
                    },
                },
                {
                    "query": {
                        "pages": [
                            {
                                "imageinfo": [
                                    {
                                        "url": "https://example.com/image.svg",
                                        "mime": "image/svg+xml",
                                        "canonicaltitle": "File:An Example Image",
                                        "descriptionurl": "https://example.com/description",
                                    },
                                ],
                            }
                        ],
                    },
                },
            ),
            # No "pageimage".
            (
                None,
                {
                    "query": {
                        "pages": [
                            {},
                        ]
                    }
                },
                None,
            ),
        ],
    )
    async def test_get_image__should_return(
        self,
        expected: bool,
        page_response_json: Mapping[str, Any],
        file_response_json: Mapping[str, Any] | None,
        http_client_mock: aioresponses,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")

        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        file_url = "https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:Amsterdam%20%26%20Omstreken&iiprop=url|mime|canonicaltitle&format=json&formatversion=2"
        image_url = "https://example.com/image.svg"
        image_data = bytes(123)

        download_directory_path = tmp_path / "download"
        http_client_mock.get(page_url, body=dumps(page_response_json))
        http_client_mock.get(file_url, body=dumps(file_response_json))
        http_client_mock.get(image_url, body=image_data)
        async with ClientSession() as http_client:
            sut = Client(
                download_directory_path=download_directory_path,
                http_client=http_client,
                user=StaticUser(),
            )
            actual = await sut.get_image(page_language, page_name)
        if expected:
            assert actual is not None
            assert actual.media_type == SVG
            assert actual.title == "An Example Image"
            assert actual.wikimedia_commons_url == "https://example.com/description"
            assert actual.path.suffix == ".svg"
            async with aiofiles.open(actual.path, mode="rb") as image_f:
                assert await image_f.read() == image_data
        else:
            assert actual is None
