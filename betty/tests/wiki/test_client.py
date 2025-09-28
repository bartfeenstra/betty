from __future__ import annotations

from json import dumps
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from geopy import Point
from multidict import CIMultiDict

from betty.fetch import FetchResponse
from betty.fetch.static import StaticFetcher
from betty.media_type.media_types import SVG
from betty.test_utils.user import StaticUser
from betty.wiki.client import Client, Image, Summary

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_mock import MockerFixture

    from betty.cache.file import BinaryFileCache


def _new_json_fetch_response(json_data: Any) -> FetchResponse:
    return FetchResponse(CIMultiDict(), dumps(json_data).encode("utf-8"), "utf-8")


class TestSummary:
    async def test_url(self) -> None:
        sut = Summary("nl", "Amsterdam", "Title for Amsterdam", "Content for Amsterdam")
        assert sut.url == "https://nl.wikipedia.org/wiki/Amsterdam"


class TestClient:
    @pytest.mark.parametrize(
        ("expected", "fetch_json"),
        [
            (
                {},
                {},
            ),
            (
                {},
                {
                    "query": {},
                },
            ),
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
        fetch_json: Mapping[str, Any],
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        fetch_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        fetcher = StaticFetcher(
            fetch_map={fetch_url: _new_json_fetch_response(fetch_json)}
        )
        translations = await Client(fetcher, user=StaticUser()).get_translations(
            page_language, page_name
        )
        assert expected == translations

    async def test_get_translations__with_invalid_json_response_should_return_none(
        self,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        fetch_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks&lllimit=500&format=json&formatversion=2"
        fetcher = StaticFetcher(
            fetch_map={
                fetch_url: FetchResponse(
                    CIMultiDict(),
                    b"{Haha Im not rly JSON}",
                    "utf-8",
                )
            }
        )
        actual = await Client(fetcher, user=StaticUser()).get_translations(
            page_language, page_name
        )
        assert actual == {}

    @pytest.mark.parametrize(
        "response_json",
        [
            {},
            {"query": {}},
            {"query": {"pages": {}}},
            {"query": {"pages": []}},
        ],
    )
    async def test_get_translations__with_unexpected_json_response_should_return_none(
        self,
        response_json: Mapping[str, Any],
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        fetch_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstrekens&prop=langlinks&lllimit=500&format=json&formatversion=2"
        fetcher = StaticFetcher(
            fetch_map={fetch_url: _new_json_fetch_response(response_json)}
        )
        actual = await Client(fetcher, user=StaticUser()).get_translations(
            page_language, page_name
        )
        assert actual == {}

    @pytest.mark.parametrize(
        ("expected", "fetch_json"),
        [
            # Missing keys in the fetch response.
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
            # Success.
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
        expected: Summary | None,
        fetch_json: Mapping[str, Any],
        binary_file_cache: BinaryFileCache,
    ) -> None:
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        fetch_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam & Omstreken"
        )
        fetcher = StaticFetcher(
            fetch_map={fetch_url: _new_json_fetch_response(fetch_json)}
        )
        client = Client(fetcher, user=StaticUser())
        actual = await client.get_summary(page_language, page_name)
        assert actual == expected

    @pytest.mark.parametrize(
        ("expected", "fetch_json"),
        [
            # Missing keys in the fetch response.
            (
                None,
                {},
            ),
            (
                None,
                {
                    "query": {},
                },
            ),
            (
                None,
                {
                    "query": {
                        "pages": [],
                    },
                },
            ),
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
            (
                None,
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
                None,
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
                None,
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
        fetch_json: Mapping[str, Any],
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        fetch_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        fetcher = StaticFetcher(
            fetch_map={fetch_url: _new_json_fetch_response(fetch_json)}
        )
        actual = await Client(fetcher, user=StaticUser()).get_place_coordinates(
            page_language, page_name
        )
        assert actual == expected

    @pytest.mark.parametrize(
        ("expected", "page_fetch_json", "file_fetch_json"),
        [
            # Missing JSON keys for the page API fetch.
            (
                None,
                {},
                None,
            ),
            (
                None,
                {"query": {}},
                None,
            ),
            (
                None,
                {"query": {"pages": []}},
                None,
            ),
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
            # Missing JSON keys for the file API fetch.
            (
                None,
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
                None,
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
                None,
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
                None,
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
            # A successful response.
            (
                Image(
                    Path(__file__),
                    SVG,
                    "An Example Image",
                    "https://example.com/description",
                    "example.svg",
                ),
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
                                        "url": "https://example.com/image",
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
        ],
    )
    async def test_get_image__should_return(
        self,
        expected: Image | None,
        page_fetch_json: Mapping[str, Any],
        file_fetch_json: Mapping[str, Any] | None,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
        tmp_path: Path,
    ) -> None:
        mocker.patch("sys.stderr")

        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        page_fetch_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        file_fetch_url = "https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&titles=File:Amsterdam%20%26%20Omstreken&iiprop=url|mime|canonicaltitle&format=json&formatversion=2"

        fetch_map = {page_fetch_url: _new_json_fetch_response(page_fetch_json)}
        fetch_file_map = {}
        if file_fetch_json is not None:
            fetch_map[file_fetch_url] = _new_json_fetch_response(file_fetch_json)
        image_file_path = tmp_path / "image"
        if expected is not None:
            fetch_file_map["https://example.com/image"] = image_file_path
        fetcher = StaticFetcher(fetch_map=fetch_map, fetch_file_map=fetch_file_map)

        actual = await Client(fetcher, user=StaticUser()).get_image(
            page_language, page_name
        )
        if expected is None:
            assert actual is None
        else:
            assert actual is not None
            assert actual.media_type == expected.media_type
            assert actual.title == expected.title
            assert actual.wikimedia_commons_url == expected.wikimedia_commons_url
            assert actual.path is image_file_path
