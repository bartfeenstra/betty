from __future__ import annotations

from betty.entities.link import Link
from betty.test_utils.ancestry.has_links import DummyHasLinks


class TestHasLinks:
    def test_links(self) -> None:
        link = Link("https://example.com")
        sut = DummyHasLinks(links=[link])
        assert sut.links.view == [link]
