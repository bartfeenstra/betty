from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type.media_types import HTML
from betty.privacy import Privacy
from betty.test_utils.ancestry.has_links import DummyHasLinks
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.locale.localizable import (
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.model import EntityDefinitionTestBase, EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.model import Entity
    from betty.plugin import PluginDefinition

import pytest


class TestLinkDefinition(EntityDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Link.plugin()


class TestLink(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Link("https://example.com")

    async def test___init____with_label(self) -> None:
        url = "https://example.com"
        label = "Hello, world!"
        sut = Link(url, label=label)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    def test_owner__without_owner(self) -> None:
        sut = Link("https://example.com")
        assert sut.owner is None

    def test_owner__with_owner(self) -> None:
        owner = DummyHasLinks()
        sut = Link("https://example.com", owner=owner)
        assert sut.owner is owner

    async def test_url(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.url.localize(DEFAULT_LOCALIZER) == url

    async def test_media_type(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.media_type is None

    async def test_description(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert not sut.description

    async def test_relationship(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.relationship is None

    async def test_label__without_label(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert url in sut.label.localize(DEFAULT_LOCALIZER)

    async def test_label__with_label(self) -> None:
        label = "Hello, world!"
        sut = Link("https://example.com", label=label)
        assert label in sut.label.localize(DEFAULT_LOCALIZER)

    async def test_has_label__without_label(self) -> None:
        sut = Link("https://example.com")
        assert not sut.has_label

    async def test_has_label__with_label(self) -> None:
        sut = Link("https://example.com", label=DUMMY_LOCALIZABLE)
        assert sut.has_label

    async def test_dump_linked_data__should_dump_minimal(self) -> None:
        link = Link("https://example.com")
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "id": link.id,
            "url": {
                DEFAULT_LOCALE_TAG: "https://example.com",
            },
            "owner": None,
            "private": False,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(self) -> None:
        owner = DummyHasLinks(id="O1")
        link = Link(
            "https://example.com",
            label="The Label",
            description="The Description",
            relationship="external",
            media_type=HTML,
            owner=owner,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "id": link.id,
            "url": {
                DEFAULT_LOCALE_TAG: "https://example.com",
            },
            "relationship": "external",
            "label": {
                DEFAULT_LOCALE_TAG: "The Label",
            },
            "description": {
                DEFAULT_LOCALE_TAG: "The Description",
            },
            "mediaType": "text/html",
            "owner": "/dummy-has-links/O1/index.json",
            "private": False,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
        owner = DummyHasLinks(id="O1")
        link = Link(
            "https://example.com",
            label="The Label",
            description="The Description",
            relationship="external",
            media_type=HTML,
            owner=owner,
            privacy=Privacy.PRIVATE,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "id": link.id,
            "owner": "/dummy-has-links/O1/index.json",
            "private": True,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected
