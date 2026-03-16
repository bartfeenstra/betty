from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, call

from babel import Locale
from geopy import Point

from betty.ancestry import Ancestry
from betty.ancestry.link import Link
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.locale.localize import LocalizerRepository
from betty.locale.translation import DEFAULT_TRANSLATION_REPOSITORY
from betty.media_type import MediaType
from betty.media_type.media_types import HTML
from betty.plugins.copyright_notice import WikipediaContributors
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.model import DummyEntityOne
from betty.user.no_op import NoOpUser
from betty.wiki.client import Client, Image, Summary
from betty.wiki.populator import Populator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestPopulator:
    async def test_populate__link_with_translations(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
        )
        m_client.get_translations.return_value = {
            "nl": "Amsterdam",
            "uk": "Амстердам",
        }
        m_client.get_summary.side_effect = [
            Summary("en", "Amsterdam", "Amsterdam (en)", "Amsterdam (en)"),
            Summary("nl", "Amsterdam", "Amsterdam (nl)", "Amsterdam (nl)"),
            Summary("uk", "Амстердам", "Амстердам (uk)", "Амстердам (uk)"),
        ]
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        ancestry = Ancestry(link)
        localizers = LocalizerRepository(DEFAULT_TRANSLATION_REPOSITORY)
        sut = Populator(
            ancestry,
            [Locale("en"), Locale("nl"), Locale("uk")],
            localizers,
            m_client,
            WikipediaContributors(DUMMY_LOCALIZABLE),
            user=NoOpUser(),
        )
        await sut.populate(link)
        localizer_en = localizers.get("en")
        localizer_nl = localizers.get("nl")
        localizer_uk = localizers.get("uk")
        assert (
            link.url.localize(localizer_en) == "https://en.wikipedia.org/wiki/Amsterdam"
        )
        assert (
            link.url.localize(localizer_nl) == "https://nl.wikipedia.org/wiki/Amsterdam"
        )
        assert (
            link.url.localize(localizer_uk) == "https://uk.wikipedia.org/wiki/Амстердам"
        )
        assert link.label.localize(localizer_en) == "Amsterdam (en)"
        assert link.label.localize(localizer_nl) == "Amsterdam (nl)"
        assert link.label.localize(localizer_uk) == "Амстердам (uk)"
        assert link.media_type == HTML
        assert link.relationship == "external"
        assert link.description is not None
        m_client.get_translations.assert_awaited_once_with("en", "Amsterdam")
        m_client.get_summary.assert_has_awaits(
            [
                call("en", "Amsterdam"),
                call("nl", "Amsterdam"),
                call("uk", "Амстердам"),
            ]
        )

    async def test_populate__link_without_translations(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
        )
        m_client.get_translations.return_value = {}
        m_client.get_summary.side_effect = [
            Summary("en", "Amsterdam", "Amsterdam (en)", "Amsterdam (en)"),
            Summary("nl", "Amsterdam", "Amsterdam (nl)", "Amsterdam (nl)"),
            Summary("uk", "Амстердам", "Амстердам (uk)", "Амстердам (uk)"),
        ]
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        ancestry = Ancestry(link)
        localizers = LocalizerRepository(DEFAULT_TRANSLATION_REPOSITORY)
        sut = Populator(
            ancestry,
            [Locale("en"), Locale("nl"), Locale("uk")],
            localizers,
            m_client,
            WikipediaContributors(DUMMY_LOCALIZABLE),
            user=NoOpUser(),
        )
        await sut.populate(link)
        localizer_en = localizers.get("en")
        assert (
            link.url.localize(localizer_en) == "http://en.wikipedia.org/wiki/Amsterdam"
        )
        assert link.media_type == HTML
        assert link.relationship == "external"
        assert link.description is not None
        m_client.get_translations.assert_awaited_once_with("en", "Amsterdam")

    async def test_populate__link_without_wikipedia_url(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
        )
        link = Link("https://example.com")
        ancestry = Ancestry(link)
        localizers = LocalizerRepository(DEFAULT_TRANSLATION_REPOSITORY)
        sut = Populator(
            ancestry,
            [Locale("en"), Locale("nl"), Locale("uk")],
            localizers,
            m_client,
            WikipediaContributors(DUMMY_LOCALIZABLE),
            user=NoOpUser(),
        )
        await sut.populate(link)

    async def test_populate__should_ignore_resource_without_link_support(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        Source("The Source")
        entity = DummyEntityOne()
        ancestry = Ancestry(entity)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(DEFAULT_TRANSLATION_REPOSITORY),
            m_client,
            WikipediaContributors(DUMMY_LOCALIZABLE),
            user=NoOpUser(),
        )
        await sut.populate(entity)

    async def test_populate__place_should_add_coordinates(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Almelo"
        coordinates = Point(52.35, 6.66666667)
        m_client.get_place_coordinates.return_value = coordinates
        m_client.get_image.return_value = None
        summary = Summary("en", "Lipsum", "Lorem ipsum", "Lorem ipsum dolor sit amet")
        m_client.get_summary.return_value = summary

        wikipedia_link = Link(f"https://{page_language}.wikipedia.org/wiki/{page_name}")
        other_link = Link("https://example.com")
        place = Place(links=[wikipedia_link, other_link])
        ancestry = Ancestry(place)
        sut = Populator(
            ancestry,
            [Locale("en")],
            LocalizerRepository(DEFAULT_TRANSLATION_REPOSITORY),
            m_client,
            WikipediaContributors(DUMMY_LOCALIZABLE),
            user=NoOpUser(),
        )
        await sut.populate(place)

        assert coordinates is place.coordinates

    async def test_populate_has_file_references_and_links(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
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
        m_client.get_image.return_value = image
        summary = Summary("en", "Lipsum", "Lorem ipsum", "Lorem ipsum dolor sit amet")
        m_client.get_summary.return_value = summary

        link = Link(f"https://{page_language}.wikipedia.org/wiki/{page_name}")
        has_file_references_and_links = Place(links=[link])
        ancestry = Ancestry(has_file_references_and_links)
        sut = Populator(
            ancestry,
            [Locale("en")],
            LocalizerRepository(DEFAULT_TRANSLATION_REPOSITORY),
            m_client,
            WikipediaContributors(DUMMY_LOCALIZABLE),
            user=NoOpUser(),
        )
        await sut.populate(has_file_references_and_links)

        file_reference = list(has_file_references_and_links.file_references)[0]
        assert file_reference.file.path == image.path
