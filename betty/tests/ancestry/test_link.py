from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import CountablePlain, Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type.media_types import HTML
from betty.model import EntityDefinition
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityDefinitionTestBase
from betty.user import UserFacing

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.plugin import PluginDefinition

import pytest


@EntityDefinition(
    id="dummy-user-facing-has-links",
    label=Plain(""),
    label_plural=Plain(""),
    label_countable=CountablePlain("", ""),
)
class DummyUserFacingHasLinks(UserFacing, HasLinks):
    pass


class TestLinkDefinition(EntityDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Link.plugin


class TestLink:
    async def test___init____with_label(self) -> None:
        url = "https://example.com"
        label = "Hello, world!"
        sut = Link(url, label=Plain(label))
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    def test_owner__without_owner(self) -> None:
        sut = Link("https://example.com")
        assert sut.owner is None

    def test_owner__with_owner(self) -> None:
        owner = DummyUserFacingHasLinks()
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

    async def test_label(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.label is not None

    async def test_has_label__without_label(self) -> None:
        sut = Link("https://example.com")
        assert not sut.has_label

    async def test_has_label__with_label(self) -> None:
        sut = Link("https://example.com", label=Plain(""))
        assert sut.has_label

    async def test_dump_linked_data__should_dump_minimal(self) -> None:
        link = Link("https://example.com")
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "id": link.id,
            "url": {
                DEFAULT_LOCALE: "https://example.com",
            },
            "owner": None,
            "private": False,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(self) -> None:
        owner = DummyUserFacingHasLinks(id="O1")
        link = Link(
            "https://example.com",
            label=Plain("The Label"),
            description=Plain("The Description"),
            relationship="external",
            media_type=HTML,
            owner=owner,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "id": link.id,
            "url": {
                DEFAULT_LOCALE: "https://example.com",
            },
            "relationship": "external",
            "label": {
                DEFAULT_LOCALE: "The Label",
            },
            "description": {
                DEFAULT_LOCALE: "The Description",
            },
            "mediaType": "text/html",
            "owner": "/dummy-user-facing-has-links/O1/index.json",
            "private": False,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
        owner = DummyUserFacingHasLinks(id="O1")
        link = Link(
            "https://example.com",
            label=Plain("The Label"),
            description=Plain("The Description"),
            relationship="external",
            media_type=HTML,
            owner=owner,
            private=True,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "id": link.id,
            "owner": "/dummy-user-facing-has-links/O1/index.json",
            "private": True,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected
