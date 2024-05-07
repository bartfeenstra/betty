from __future__ import annotations

from json import dumps
from pathlib import Path
from time import sleep
from typing import Any
from unittest.mock import call

import aiohttp
import pytest
from geopy import Point
from pytest_mock import MockerFixture

from betty.app import App
from betty.cache.file import BinaryFileCache
from betty.cache.memory import MemoryCache
from betty.locale import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.project import LocaleConfiguration

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from aioresponses import aioresponses

from betty.model.ancestry import Source, Link, Citation, Place
from betty.wikipedia import (
    Summary,
    _Retriever,
    NotAPageError,
    _parse_url,
    _Populator,
    Image,
)


class TestParseUrl:
    @pytest.mark.parametrize(
        "expected, url",
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
                "http://en.wikipedia.org/wiki/Amsterdam",
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
        assert "https://nl.wikipedia.org/wiki/Amsterdam" == sut.url

    async def test_title(self) -> None:
        title = "Title for Amsterdam"
        sut = Summary("nl", "Amsterdam", title, "Content for Amsterdam")
        assert title == sut.title

    async def test_content(self) -> None:
        content = "Content for Amsterdam"
        sut = Summary("nl", "Amsterdam", "Title for Amsterdam", content)
        assert content == sut.content


class TestRetriever:
    @pytest.mark.parametrize(
        "expected, response_pages_json",
        [
            (
                {},
                {},
            ),
            (
                {
                    "nl": "Amsterdam",
                    "uk": "Амстердам",
                },
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
                },
            ),
        ],
    )
    async def test_get_translations_should_return(
        self,
        expected: dict[str, str],
        response_pages_json: dict[str, Any],
        aioresponses: aioresponses,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        api_response_body = {
            "query": {
                "pages": [response_pages_json],
            },
        }
        aioresponses.get(api_url, body=dumps(api_response_body).encode("utf-8"))
        async with aiohttp.ClientSession() as session:
            translations = await _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
            ).get_translations(page_language, page_name)
        assert expected == translations

    async def test_get_translations_with_client_error_should_raise_retrieval_error(
        self,
        aioresponses: aioresponses,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks&lllimit=500&format=json&formatversion=2"
        aioresponses.get(api_url, exception=aiohttp.ClientError())
        async with aiohttp.ClientSession() as session:
            actual = await _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
            ).get_translations(page_language, page_name)
            assert {} == actual

    async def test_get_translations_with_invalid_json_response_should_return_none(
        self,
        aioresponses: aioresponses,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks&lllimit=500&format=json&formatversion=2"
        aioresponses.get(api_url, body="{Haha Im not rly JSON}")
        async with aiohttp.ClientSession() as session:
            actual = await _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
            ).get_translations(page_language, page_name)
            assert {} == actual

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
        response_json: dict[str, Any],
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
        aioresponses: aioresponses,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstrekens&prop=langlinks&lllimit=500&format=json&formatversion=2"

        aioresponses.get(api_url, body=dumps(response_json).encode("utf-8"))
        async with aiohttp.ClientSession() as session:
            actual = await _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
            ).get_translations(page_language, page_name)
            assert {} == actual

    @pytest.mark.parametrize(
        "extract_key",
        [
            "extract",
            "extract_html",
        ],
    )
    async def test_get_summary_should_return(
        self,
        extract_key: str,
        aioresponses: aioresponses,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam & Omstreken"
        )
        summary_url = "https://en.wikipedia.org/wiki/Amsterdam & Omstreken"
        title = "Amstelredam"
        extract_1 = "De hoofdstad van Nederland."
        extract_4 = "Niet de hoofdstad van Holland."
        api_response_body_1 = {
            "titles": {
                "normalized": title,
            },
            extract_key: extract_1,
        }
        api_response_body_4 = {
            "titles": {
                "normalized": title,
            },
            extract_key: extract_4,
        }
        aioresponses.get(api_url, body=dumps(api_response_body_1).encode("utf-8"))
        aioresponses.get(api_url, exception=aiohttp.ClientError())
        aioresponses.get(api_url, body=dumps(api_response_body_4).encode("utf-8"))
        async with aiohttp.ClientSession() as session:
            retriever = _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
                1,
            )
            # The first retrieval should make a successful request and set the cache.
            summary_1 = await retriever.get_summary(page_language, page_name)
            # The second retrieval should hit the cache from the first request.
            summary_2 = await retriever.get_summary(page_language, page_name)
            # The third retrieval should result in a failed request, and hit the cache from the first request.
            sleep(2)
            summary_3 = await retriever.get_summary(page_language, page_name)
            # The fourth retrieval should make a successful request and set the cache again.
            summary_4 = await retriever.get_summary(page_language, page_name)
            # The fifth retrieval should hit the cache from the fourth request.
            summary_5 = await retriever.get_summary(page_language, page_name)
        for summary in [summary_1, summary_2, summary_3]:
            assert summary
            assert summary_url == summary.url
            assert title == summary.title
            assert extract_1 == summary.content
        for summary in [summary_4, summary_5]:
            assert summary
            assert summary_url == summary.url
            assert title == summary.title
            assert extract_4 == summary.content

    async def test_get_summary_with_client_error_should_raise_retrieval_error(
        self,
        aioresponses: aioresponses,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=extracts&exintro&format=json&formatversion=2"
        aioresponses.get(api_url, exception=aiohttp.ClientError())
        async with aiohttp.ClientSession() as session:
            retriever = _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
            )
            actual = await retriever.get_summary(page_language, page_name)
            assert None is actual

    @pytest.mark.parametrize(
        "expected, response_pages_json",
        [
            (
                None,
                {},
            ),
            # Almelo.
            (
                Point(52.35, 6.66666667),
                {
                    "coordinates": [
                        {
                            "lat": 52.35,
                            "lon": 6.66666667,
                            "primary": True,
                            "globe": "earth",
                        },
                    ],
                },
            ),
            # Tranquility Base.
            (
                None,
                {
                    "coordinates": [
                        {
                            "lat": 0.6875,
                            "lon": 23.43333333,
                            "primary": True,
                            "globe": "moon",
                        },
                    ],
                },
            ),
        ],
    )
    async def test_get_place_coordinates_should_return(
        self,
        expected: Point | None,
        response_pages_json: dict[str, Any],
        aioresponses: aioresponses,
        mocker: MockerFixture,
        binary_file_cache: BinaryFileCache,
    ) -> None:
        mocker.patch("sys.stderr")
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        api_url = "https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam%20%26%20Omstreken&prop=langlinks|pageimages|coordinates&lllimit=500&piprop=name&pilicense=free&pilimit=1&coprimary=primary&format=json&formatversion=2"
        api_response_body = {
            "query": {
                "pages": [response_pages_json],
            },
        }
        aioresponses.get(api_url, body=dumps(api_response_body).encode("utf-8"))
        async with aiohttp.ClientSession() as session:
            actual = await _Retriever(
                session,
                MemoryCache[Any](DEFAULT_LOCALIZER),
                binary_file_cache,
            ).get_place_coordinates(page_language, page_name)
        assert expected == actual


class TestPopulator:
    async def test_populate_link_should_convert_http_to_https(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        page_language = "nl"
        async with App.new_temporary() as app, app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, page_language)
        assert "https://en.wikipedia.org/wiki/Amsterdam" == link.url

    @pytest.mark.parametrize(
        "expected, media_type",
        [
            (MediaType("text/plain"), MediaType("text/plain")),
            (MediaType("text/html"), MediaType("text/html")),
            (MediaType("text/html"), None),
        ],
    )
    async def test_populate_link_should_set_media_type(
        self,
        expected: MediaType,
        media_type: MediaType | None,
        mocker: MockerFixture,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link(
            "http://en.wikipedia.org/wiki/Amsterdam",
            media_type=media_type,
        )
        async with App.new_temporary() as app, app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, "en")
        assert expected == link.media_type

    @pytest.mark.parametrize(
        "expected, relationship",
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
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        link.relationship = relationship
        async with App.new_temporary() as app, app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, "en")
        assert expected == link.relationship

    @pytest.mark.parametrize(
        "expected, page_language, locale",
        [
            ("nl-NL", "nl", "nl-NL"),
            ("nl", "nl", None),
            ("nl", "en", "nl"),
        ],
    )
    async def test_populate_link_should_set_locale(
        self,
        expected: str,
        page_language: str,
        locale: str | None,
        mocker: MockerFixture,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://%s.wikipedia.org/wiki/Amsterdam" % page_language)
        link.locale = locale
        async with App.new_temporary() as app, app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, page_language)
        assert expected == link.locale

    @pytest.mark.parametrize(
        "expected, description",
        [
            ("This is the original description", "This is the original description"),
            ("Read more on Wikipedia.", None),
        ],
    )
    async def test_populate_link_should_set_description(
        self,
        expected: str,
        description: str,
        mocker: MockerFixture,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link(
            "http://en.wikipedia.org/wiki/Amsterdam",
            description=description,
        )
        page_language = "en"
        async with App.new_temporary() as app, app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, page_language)
        assert expected == link.description

    @pytest.mark.parametrize(
        "expected, label",
        [
            ("Amsterdam", "Amsterdam"),
            ("The city of Amsterdam", None),
        ],
    )
    async def test_populate_link_should_set_label(
        self,
        expected: str,
        label: str | None,
        mocker: MockerFixture,
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        link.label = label
        summary = Summary(
            "en",
            "The_city_of_Amsterdam",
            "The city of Amsterdam",
            "Amsterdam, such a lovely place!",
        )
        async with App.new_temporary() as app, app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, "en", summary)
        assert expected == link.label

    async def test_populate_should_ignore_resource_without_link_support(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        source = Source("The Source")
        resource = Citation(
            id="the_citation",
            source=source,
        )
        async with App.new_temporary() as app, app:
            app.project.ancestry.add(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()

    async def test_populate_should_ignore_resource_without_links(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        resource = Source(
            id="the_source",
            name="The Source",
        )
        async with App.new_temporary() as app, app:
            app.project.ancestry.add(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()
        assert [] == resource.links

    async def test_populate_should_ignore_non_wikipedia_links(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch("betty.wikipedia._Retriever")
        link = Link("https://example.com")
        resource = Source(
            id="the_source",
            name="The Source",
            links=[link],
        )
        async with App.new_temporary() as app, app:
            app.project.ancestry.add(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()
        assert [link] == resource.links

    async def test_populate_should_populate_existing_link(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        summary_title = "Amsterdam"
        summary_content = "Capitol of the Netherlands"
        summary = Summary(page_language, page_name, summary_title, summary_content)
        m_retriever.get_summary.return_value = summary
        m_retriever.get_image.return_value = None

        link = Link("https://en.wikipedia.org/wiki/Amsterdam & Omstreken")
        resource = Source(
            id="the_source",
            name="The Source",
            links=[link],
        )
        async with App.new_temporary() as app, app:
            app.project.ancestry.add(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()
        m_retriever.get_summary.assert_called_once_with(page_language, page_name)
        assert 1 == len(resource.links)
        assert "Amsterdam" == link.label
        assert "en" == link.locale
        assert MediaType("text/html") == link.media_type
        assert link.description is not None
        assert "external" == link.relationship

    async def test_populate_should_add_translation_links(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        summary_title = "Amsterdam"
        summary_content = "Capitol of the Netherlands"
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
        async with App.new_temporary() as app, app:
            app.project.configuration.locales["en-US"].alias = "en"
            app.project.configuration.locales.append(
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                )
            )
            app.project.ancestry.add(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()

        m_retriever.get_summary.assert_has_calls(
            [
                call(page_language, page_name),
                call(added_page_language, added_page_name),
            ]
        )
        m_retriever.get_translations.assert_called_once_with(page_language, page_name)
        assert 2 == len(resource.links)
        link_nl = [link for link in resource.links if link != link_en][0]
        assert "Amsterdam" == link_nl.label
        assert "nl" == link_nl.locale
        assert MediaType("text/html") == link_nl.media_type
        assert link_nl.description is not None
        assert "external" == link_nl.relationship

    async def test_populate_place_should_add_coordinates(
        self, mocker: MockerFixture
    ) -> None:
        m_retriever = mocker.patch(
            "betty.wikipedia._Retriever", spec=_Retriever, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Almelo"
        coordinates = Point(52.35, 6.66666667)
        m_retriever.get_place_coordinates.return_value = coordinates
        m_retriever.get_image.return_value = None

        link = Link(f"https://{page_language}.wikipedia.org/wiki/{page_name}")
        place = Place(links=[link])
        async with App.new_temporary() as app, app:
            app.project.ancestry.add(place)
            sut = _Populator(app, m_retriever)
            await sut.populate()

        assert coordinates is place.coordinates

    async def test_populate_has_links(
        self, aioresponses: aioresponses, mocker: MockerFixture
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
        )
        m_retriever.get_image.return_value = image

        link = Link(f"https://{page_language}.wikipedia.org/wiki/{page_name}")
        place = Place(links=[link])
        async with App.new_temporary() as app, app:
            app.project.ancestry.add(place)
            sut = _Populator(app, m_retriever)
            await sut.populate()

        assert place.files[0].path == image.path
