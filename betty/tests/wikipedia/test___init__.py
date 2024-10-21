from __future__ import annotations

from json import dumps
from pathlib import Path
from typing import Any, TYPE_CHECKING
from unittest.mock import AsyncMock, call

import pytest
from geopy import Point
from multidict import CIMultiDict

from betty.ancestry import Ancestry
from betty.ancestry.citation import Citation
from betty.ancestry.link import Link
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.assets import AssetRepository
from betty.fetch import FetchResponse
from betty.fetch.static import StaticFetcher
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER, LocalizerRepository
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, PLAIN_TEXT, SVG
from betty.wikipedia import (
    Summary,
    _Retriever,
    NotAPageError,
    _parse_url,
    _Populator,
    Image,
)
from betty.wikipedia.copyright_notice import WikipediaContributors

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.cache.file import BinaryFileCache
    from pytest_mock import MockerFixture


def _new_json_fetch_response(json_data: Any) -> FetchResponse:
    return FetchResponse(CIMultiDict(), dumps(json_data).encode("utf-8"), "utf-8")


class TestParseUrl:
    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            (
                ("en", "Amsterdam"),
                "http://en.wikipedia.org/wiki/Amsterdam",
            ),
            (
                ("nl", "Amsterdam"),
                "https://nl.wikipedia.org/wiki/Amsterdam",
            ),
            (
                ("en", "Amsterdam"),
                "https://en.wikipedia.org/wiki/Amsterdam/",
            ),
            (
                ("en", "Amsterdam"),
                "https://en.wikipedia.org/wiki/Amsterdam/some-path",
            ),
            (
                ("en", "Amsterdam"),
                "https://en.wikipedia.org/wiki/Amsterdam?some=query",
            ),
            (
                ("en", "Amsterdam"),
                "https://en.wikipedia.org/wiki/Amsterdam#some-fragment",
            ),
        ],
    )
    async def test_should_return(self, expected: tuple[str, str], url: str) -> None:
        assert expected == _parse_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "ftp://en.wikipedia.org/wiki/Amsterdam",
            "https://en.wikipedia.org/w/index.php?title=Amsterdam&action=edit",
        ],
    )
    async def test_should_error(self, url: str) -> None:
        with pytest.raises(NotAPageError):
            _parse_url(url)


class TestSummary:
    async def test_url(self) -> None:
        sut = Summary("nl", "Amsterdam", "Title for Amsterdam", "Content for Amsterdam")
        assert sut.url == "https://nl.wikipedia.org/wiki/Amsterdam"


class TestRetriever:
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
    async def test_get_translations_should_return(
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
        translations = await _Retriever(fetcher).get_translations(
            page_language, page_name
        )
        assert expected == translations

    async def test_get_translations_with_invalid_json_response_should_return_none(
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
                    "{Haha Im not rly JSON}".encode("utf-8"),
                    "utf-8",
                )
            }
        )
        actual = await _Retriever(fetcher).get_translations(page_language, page_name)
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
    async def test_get_translations_with_unexpected_json_response_should_return_none(
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
        actual = await _Retriever(fetcher).get_translations(page_language, page_name)
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
    async def test_get_summary_should_return(
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
        retriever = _Retriever(fetcher)
        actual = await retriever.get_summary(page_language, page_name)
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
    async def test_get_place_coordinates_should_return(
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
        actual = await _Retriever(fetcher).get_place_coordinates(
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
    async def test_get_image_should_return(
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

        actual = await _Retriever(fetcher).get_image(page_language, page_name)
        if expected is None:
            assert actual is None
        else:
            assert actual is not None
            assert actual.media_type == expected.media_type
            assert actual.title == expected.title
            assert actual.wikimedia_commons_url == expected.wikimedia_commons_url
            assert actual.path is image_file_path


class TestPopulator:
    async def test_populate_link_should_convert_http_to_https(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        page_language = "nl"
        sut = _Populator(
            await Ancestry.new(),
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate_link(link, page_language)
        assert link.url == "https://en.wikipedia.org/wiki/Amsterdam"

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            (PLAIN_TEXT, PLAIN_TEXT),
            (HTML, HTML),
            (HTML, None),
        ],
    )
    async def test_populate_link_should_set_media_type(
        self,
        expected: MediaType,
        media_type: MediaType | None,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link(
            "http://en.wikipedia.org/wiki/Amsterdam",
            media_type=media_type,
        )
        sut = _Populator(
            await Ancestry.new(),
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate_link(link, "en")
        assert expected == link.media_type

    @pytest.mark.parametrize(
        ("expected", "relationship"),
        [
            ("alternate", "alternate"),
            ("external", "external"),
            ("external", None),
        ],
    )
    async def test_populate_link_should_set_relationship(
        self,
        expected: str,
        relationship: str | None,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        link.relationship = relationship
        sut = _Populator(
            await Ancestry.new(),
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate_link(link, "en")
        assert expected == link.relationship

    @pytest.mark.parametrize(
        ("expected", "page_language", "original_link_locale"),
        [
            ("nl-NL", "nl", "nl-NL"),
            ("nl", "nl", UNDETERMINED_LOCALE),
            ("nl", "en", "nl"),
        ],
    )
    async def test_populate_link_should_set_locale(
        self,
        expected: str,
        page_language: str,
        original_link_locale: str,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link(f"http://{page_language}.wikipedia.org/wiki/Amsterdam")
        link.locale = original_link_locale
        sut = _Populator(
            await Ancestry.new(),
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate_link(link, page_language)
        assert expected == link.locale

    @pytest.mark.parametrize(
        ("expected", "description"),
        [
            ("This is the original description", "This is the original description"),
            ("Read more on Wikipedia.", None),
        ],
    )
    async def test_populate_link_should_set_description(
        self, expected: str, description: str, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link(
            "http://en.wikipedia.org/wiki/Amsterdam",
            description=description,
        )
        page_language = "en"
        sut = _Populator(
            await Ancestry.new(),
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate_link(link, page_language)
        assert link.description.localize(DEFAULT_LOCALIZER) == expected

    @pytest.mark.parametrize(
        ("expected", "label"),
        [
            ("Amsterdam", "Amsterdam"),
            ("The city of Amsterdam", None),
        ],
    )
    async def test_populate_link_should_set_label(
        self, expected: str, label: str | None, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        if label:
            link.label = label
        summary = Summary(
            "en",
            "The_city_of_Amsterdam",
            "The city of Amsterdam",
            "Amsterdam, such a lovely place!",
        )
        sut = _Populator(
            await Ancestry.new(),
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate_link(link, "en", summary)
        assert link.label.localize(DEFAULT_LOCALIZER) == expected

    async def test_populate_should_ignore_resource_without_link_support(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        source = Source("The Source")
        resource = Citation(
            id="the_citation",
            source=source,
        )
        ancestry = await Ancestry.new()
        ancestry.add(resource)
        sut = _Populator(
            ancestry,
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()

    async def test_populate_should_ignore_resource_without_links(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        resource = Source(
            id="the_source",
            name="The Source",
        )
        ancestry = await Ancestry.new()
        ancestry.add(resource)
        sut = _Populator(
            ancestry,
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()
        assert resource.links == []

    async def test_populate_should_ignore_non_wikipedia_links(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("https://example.com")
        resource = Source(
            id="the_source",
            name="The Source",
            links=[link],
        )
        ancestry = await Ancestry.new()
        ancestry.add(resource)
        sut = _Populator(
            ancestry,
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()
        assert [link] == resource.links

    async def test_populate_should_populate_existing_link(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        summary_title = "Amsterdam"
        summary_content = "Capital of the Netherlands"
        summary = Summary(page_language, page_name, summary_title, summary_content)
        m_retriever.get_summary.return_value = summary
        m_retriever.get_image.return_value = None

        link = Link("https://en.wikipedia.org/wiki/Amsterdam & Omstreken")
        resource = Source(
            id="the_source",
            name="The Source",
            links=[link],
        )
        ancestry = await Ancestry.new()
        ancestry.add(resource)
        sut = _Populator(
            ancestry,
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()
        m_retriever.get_summary.assert_called_once_with(page_language, page_name)
        assert len(resource.links) == 1
        assert link.label.localize(DEFAULT_LOCALIZER) == "Amsterdam"
        assert link.locale == "en"
        assert link.media_type == HTML
        assert link.description is not None
        assert link.relationship == "external"

    async def test_populate_should_add_translation_links(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        summary_title = "Amsterdam"
        summary_content = "Capital of the Netherlands"
        summary = Summary(page_language, page_name, summary_title, summary_content)
        added_page_language = "nl"
        added_page_name = "Amsterdam & Omstreken"
        added_summary_title = "Amsterdam"
        added_summary_content = "Hoofdstad van Nederland"
        added_summary = Summary(
            added_page_language,
            added_page_name,
            added_summary_title,
            added_summary_content,
        )
        m_retriever.get_summary.side_effect = [summary, added_summary]
        m_retriever.get_image.return_value = None
        m_retriever.get_translations.return_value = {
            page_language: page_name,
            added_page_language: added_page_name,
        }

        link_en = Link("https://en.wikipedia.org/wiki/Amsterdam & Omstreken")
        resource = Source(
            id="the_source",
            name="The Source",
            links=[link_en],
        )
        ancestry = await Ancestry.new()
        ancestry.add(resource)
        sut = _Populator(
            ancestry,
            ["en-US", "nl-NL"],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()

        m_retriever.get_summary.assert_has_calls(
            [
                call(page_language, page_name),
                call(added_page_language, added_page_name),
            ]
        )
        m_retriever.get_translations.assert_called_once_with(page_language, page_name)
        assert len(resource.links) == 2
        link_nl = [link for link in resource.links if link != link_en][0]
        assert link_nl.label.localize(DEFAULT_LOCALIZER) == "Amsterdam"
        assert link_nl.locale == "nl"
        assert link_nl.media_type == HTML
        assert link_nl.description is not None
        assert link_nl.relationship == "external"

    async def test_populate_place_should_add_coordinates(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Almelo"
        coordinates = Point(52.35, 6.66666667)
        m_retriever.get_place_coordinates.return_value = coordinates
        m_retriever.get_image.return_value = None
        summary = Summary("en", "Lipsum", "Lorem ipsum", "Lorem ipsum dolor sit amet")
        m_retriever.get_summary.return_value = summary

        wikipedia_link = Link(f"https://{page_language}.wikipedia.org/wiki/{page_name}")
        other_link = Link("https://example.com")
        place = Place(links=[wikipedia_link, other_link])
        ancestry = await Ancestry.new()
        ancestry.add(place)
        sut = _Populator(
            ancestry,
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()

        assert coordinates is place.coordinates

    async def test_populate_has_links(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Almelo"
        image = Image(
            Path(__file__),
            MediaType("application/octet-stream"),
            "",
            "https://example.com",
            "example",
        )
        m_retriever.get_image.return_value = image
        summary = Summary("en", "Lipsum", "Lorem ipsum", "Lorem ipsum dolor sit amet")
        m_retriever.get_summary.return_value = summary

        link = Link(f"https://{page_language}.wikipedia.org/wiki/{page_name}")
        place = Place(links=[link])
        ancestry = await Ancestry.new()
        ancestry.add(place)
        sut = _Populator(
            ancestry,
            [],
            LocalizerRepository(AssetRepository(tmp_path / "assets")),
            m_retriever,
            WikipediaContributors({}),
        )
        await sut.populate()

        file_reference = place.file_references[0]
        assert file_reference.file.path == image.path
