from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.entities.link import Link
from betty.locale import default_locale_tag
from betty.localizer import default_localizer
from betty.media_types.html import HTML
from betty.privacy import Privacy
from betty.test_utils.ancestry.has_links import DummyHasLinks
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.entity import Entity
    from betty.test_utils.conftest import AssertDumpsLinkedData

import pytest


class TestLink(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Link("https://example.com")

    def test___init____with_label(self) -> None:
        url = "https://example.com"
        label = "Hello, world!"
        sut = Link(url, label=label)
        assert sut.label.localize(default_localizer) == label

    def test_owner__without_owner(self) -> None:
        sut = Link("https://example.com")
        assert sut.owner is None

    def test_owner__with_owner(self) -> None:
        owner = DummyHasLinks()
        sut = Link("https://example.com", owner=owner)
        assert sut.owner is owner

    def test_url(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.url.localize(default_localizer) == url

    def test_media_type(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.media_type is None

    def test_description(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert not sut.description

    def test_relationship(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.relationship is None

    def test_label__without_label(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert url in sut.label.localize(default_localizer)

    def test_label__with_label(self) -> None:
        label = "Hello, world!"
        sut = Link("https://example.com", label=label)
        assert label in sut.label.localize(default_localizer)

    def test_has_label__without_label(self) -> None:
        sut = Link("https://example.com")
        assert not sut.has_label

    def test_has_label__with_label(self) -> None:
        sut = Link("https://example.com", label="-")
        assert sut.has_label

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        link = Link(
            "https://example.com",
            id="my-first-link",
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "@id": "https://example.com/link/my-first-link/index.json",
            "id": "my-first-link",
            "url": {
                default_locale_tag: "https://example.com",
            },
            "owner": None,
            "privacy": False,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        owner = DummyHasLinks(id="my-first-has-links")
        link = Link(
            "https://example.com",
            id="my-first-link",
            label="The Label",
            description="The Description",
            relationship="external",
            media_type=HTML,
            owner=owner,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "@id": "https://example.com/link/my-first-link/index.json",
            "id": "my-first-link",
            "url": {
                default_locale_tag: "https://example.com",
            },
            "relationship": "external",
            "label": {
                default_locale_tag: "The Label",
            },
            "description": {
                default_locale_tag: "The Description",
            },
            "mediaType": "text/html",
            "owner": "/dummy-has-links/my-first-has-links/index.json",
            "privacy": False,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        owner = DummyHasLinks(id="my-first-has-links")
        link = Link(
            "https://example.com",
            id="my-first-link",
            label="The Label",
            description="The Description",
            relationship="external",
            media_type=HTML,
            owner=owner,
            privacy=Privacy.PRIVATE,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "@id": "https://example.com/link/my-first-link/index.json",
            "id": "my-first-link",
            "owner": "/dummy-has-links/my-first-has-links/index.json",
            "privacy": True,
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected
