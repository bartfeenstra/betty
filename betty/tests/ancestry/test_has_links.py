from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE_TAG
from betty.test_utils.ancestry.has_links import DummyHasLinks
from betty.test_utils.json.linked_data import assert_dumps_linked_data

if TYPE_CHECKING:
    from betty.portable import PortableMapping


class TestHasLinks:
    def test___init____with_links(self) -> None:
        link = Link("https://example.com")
        sut = DummyHasLinks(links=[link])
        assert sut.links.view == [link]

    def test_links(self) -> None:
        sut = DummyHasLinks()
        assert sut.links is sut.links

    async def test_dump_linked_data_without_links(self) -> None:
        sut = DummyHasLinks()
        expected: PortableMapping = {
            "id": sut.id,
            "links": [],
        }
        assert await assert_dumps_linked_data(sut) == expected

    async def test_dump_linked_data(self) -> None:
        link = Link("https://example.com")
        sut = DummyHasLinks(links=[link])
        expected = {
            "id": sut.id,
            "links": [
                {
                    "@context": {"description": "https://schema.org/description"},
                    "id": link.id,
                    "url": {
                        DEFAULT_LOCALE_TAG: "https://example.com",
                    },
                    "owner": None,
                    "private": False,
                }
            ],
        }
        assert await assert_dumps_linked_data(sut) == expected
