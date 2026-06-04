from __future__ import annotations

from typing import TYPE_CHECKING

from betty.entities.link import Link
from betty.locale import default_locale_tag
from betty.test_utils.ancestry.has_links import DummyHasLinks

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestHasLinks:
    def test___init____with_links(self) -> None:
        link = Link("https://example.com")
        sut = DummyHasLinks(links=[link])
        assert sut.links.view == [link]

    def test_links(self) -> None:
        sut = DummyHasLinks()
        assert sut.links is sut.links

    async def test_dump_linked_data_without_links(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        sut = DummyHasLinks()
        expected: PortableMapping = {
            "id": sut.id,
            "links": [],
        }
        assert await assert_dumps_linked_data(sut) == expected

    async def test_dump_linked_data(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        link = Link("https://example.com")
        sut = DummyHasLinks(links=[link])
        expected = {
            "id": sut.id,
            "links": [
                {
                    "@context": {"description": "https://schema.org/description"},
                    "id": link.id,
                    "url": {
                        default_locale_tag: "https://example.com",
                    },
                    "owner": None,
                    "privacy": False,
                }
            ],
        }
        assert await assert_dumps_linked_data(sut) == expected
