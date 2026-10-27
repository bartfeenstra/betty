from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entities.link import Link
from betty.localizer import default_localizer
from betty.test_utils.entity import EntityTestBase
from betty.test_utils.entity.associations.has_links import DummyHasLinks

if TYPE_CHECKING:
    from betty.entity import Entity


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
