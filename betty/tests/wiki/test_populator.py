from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, call

import pytest
from geopy import Point

from betty.ancestry import Ancestry
from betty.ancestry.citation import Citation
from betty.ancestry.link import Link
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import plain
from betty.locale.localizer import DEFAULT_LOCALIZER, LocalizerRepository
from betty.locale.translation import NoOpTranslationRepository
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, PLAIN_TEXT
from betty.wiki.client import Client, Image, Summary
from betty.wiki.copyright_notice import WikipediaContributors
from betty.wiki.populator import Populator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestPopulator:
    async def test_populate_link__should_convert_http_to_https(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        page_language = "nl"
        sut = Populator(
            Ancestry(),
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut._populate_link(link, page_language)
        assert link.url == "https://en.wikipedia.org/wiki/Amsterdam"

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            (PLAIN_TEXT, PLAIN_TEXT),
            (HTML, HTML),
            (HTML, None),
        ],
    )
    async def test_populate_link__should_set_media_type(
        self,
        expected: MediaType,
        media_type: MediaType | None,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link(
            "http://en.wikipedia.org/wiki/Amsterdam",
            media_type=media_type,
        )
        sut = Populator(
            Ancestry(),
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut._populate_link(link, "en")
        assert expected == link.media_type

    @pytest.mark.parametrize(
        ("expected", "relationship"),
        [
            ("alternate", "alternate"),
            ("external", "external"),
            ("external", None),
        ],
    )
    async def test_populate_link__should_set_relationship(
        self,
        expected: str,
        relationship: str | None,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        link.relationship = relationship
        sut = Populator(
            Ancestry(),
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut._populate_link(link, "en")
        assert expected == link.relationship

    @pytest.mark.parametrize(
        ("expected", "page_language", "original_link_locale"),
        [
            ("nl-NL", "nl", "nl-NL"),
            ("nl", "nl", UNDETERMINED_LOCALE),
            ("nl", "en", "nl"),
        ],
    )
    async def test_populate_link__should_set_locale(
        self,
        expected: str,
        page_language: str,
        original_link_locale: str,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link(f"http://{page_language}.wikipedia.org/wiki/Amsterdam")
        link.locale = original_link_locale
        sut = Populator(
            Ancestry(),
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut._populate_link(link, page_language)
        assert expected == link.locale

    @pytest.mark.parametrize(
        ("expected", "description"),
        [
            ("This is the original description", "This is the original description"),
            ("Read more on Wikipedia.", None),
        ],
    )
    async def test_populate_link__should_set_description(
        self,
        expected: str,
        description: str | None,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link(
            "http://en.wikipedia.org/wiki/Amsterdam",
            description=None if description is None else plain(description),
        )
        page_language = "en"
        sut = Populator(
            Ancestry(),
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut._populate_link(link, page_language)
        assert link.description is not None
        assert link.description.localize(DEFAULT_LOCALIZER) == expected

    @pytest.mark.parametrize(
        ("expected", "label"),
        [
            ("Amsterdam", "Amsterdam"),
            ("The city of Amsterdam", None),
        ],
    )
    async def test_populate_link__should_set_label(
        self,
        expected: str,
        label: str | None,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link("http://en.wikipedia.org/wiki/Amsterdam")
        if label:
            link.label = plain(label)
        summary = Summary(
            "en",
            "The_city_of_Amsterdam",
            "The city of Amsterdam",
            "Amsterdam, such a lovely place!",
        )
        sut = Populator(
            Ancestry(),
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut._populate_link(link, "en", summary)
        assert link.label.localize(DEFAULT_LOCALIZER) == expected

    async def test_populate__should_ignore_resource_without_link_support(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        source = Source(plain("The Source"))
        resource = Citation(
            id="the_citation",
            source=source,
        )
        ancestry = Ancestry()
        ancestry.add(resource)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()

    async def test_populate__should_ignore_resource_without_links(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        resource = Source(
            id="the_source",
            name=plain("The Source"),
        )
        ancestry = Ancestry()
        ancestry.add(resource)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()
        assert resource.links == []

    async def test_populate__should_ignore_non_wikipedia_links(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch("betty.wiki.client.Client")
        link = Link("https://example.com")
        resource = Source(
            id="the_source",
            name=plain("The Source"),
            links=[link],
        )
        ancestry = Ancestry()
        ancestry.add(resource)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()
        assert [link] == resource.links

    async def test_populate__should_populate_existing_link(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
        )
        page_language = "en"
        page_name = "Amsterdam & Omstreken"
        summary_title = "Amsterdam"
        summary_content = "Capital of the Netherlands"
        summary = Summary(page_language, page_name, summary_title, summary_content)
        m_client.get_summary.return_value = summary
        m_client.get_image.return_value = None

        link = Link("https://en.wikipedia.org/wiki/Amsterdam & Omstreken")
        resource = Source(
            id="the_source",
            name=plain("The Source"),
            links=[link],
        )
        ancestry = Ancestry()
        ancestry.add(resource)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()
        m_client.get_summary.assert_called_once_with(page_language, page_name)
        assert len(resource.links) == 1
        assert link.label.localize(DEFAULT_LOCALIZER) == "Amsterdam"
        assert link.locale == "en"
        assert link.media_type == HTML
        assert link.description is not None
        assert link.relationship == "external"

    async def test_populate__should_add_translation_links(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        m_client = mocker.patch(
            "betty.wiki.client.Client", spec=Client, new_callable=AsyncMock
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
        m_client.get_summary.side_effect = [summary, added_summary]
        m_client.get_image.return_value = None
        m_client.get_translations.return_value = {
            page_language: page_name,
            added_page_language: added_page_name,
        }

        link_en = Link("https://en.wikipedia.org/wiki/Amsterdam & Omstreken")
        resource = Source(
            id="the_source",
            name=plain("The Source"),
            links=[link_en],
        )
        ancestry = Ancestry()
        ancestry.add(resource)
        sut = Populator(
            ancestry,
            ["en-US", "nl-NL"],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()

        m_client.get_summary.assert_has_calls(
            [
                call(page_language, page_name),
                call(added_page_language, added_page_name),
            ]
        )
        m_client.get_translations.assert_called_once_with(page_language, page_name)
        assert len(resource.links) == 2
        link_nl = [link for link in resource.links if link != link_en][0]
        assert link_nl.label.localize(DEFAULT_LOCALIZER) == "Amsterdam"
        assert link_nl.locale == "nl"
        assert link_nl.media_type == HTML
        assert link_nl.description is not None
        assert link_nl.relationship == "external"

    async def test_populate_place__should_add_coordinates(
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
        ancestry = Ancestry()
        ancestry.add(place)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()

        assert coordinates is place.coordinates

    async def test_populate_has_links(
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
        place = Place(links=[link])
        ancestry = Ancestry()
        ancestry.add(place)
        sut = Populator(
            ancestry,
            [],
            LocalizerRepository(NoOpTranslationRepository()),
            m_client,
            WikipediaContributors({}),
        )
        await sut.populate()

        file_reference = list(place.file_references)[0]
        assert file_reference.file.path == image.path
