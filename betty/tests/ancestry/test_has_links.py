from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.locale import DEFAULT_LOCALE_TAG
from betty.model import EntityPlugin
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.locale.localizable import (
    DUMMY_LOCALIZABLE,
    _DummyCountableLocalizable,
)

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping


@EntityPlugin(
    "dummy-has-links",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=_DummyCountableLocalizable(),
)
class DummyHasLinks(HasLinks):
    pass


class TestHasLinks:
    async def test___init____with_links(self) -> None:
        link = Link("https://example.com")
        sut = DummyHasLinks(links=[link])
        assert sut.links.view == [link]

    async def test_links(self) -> None:
        sut = DummyHasLinks()
        assert sut.links is sut.links

    async def test_dump_linked_data_without_links(self) -> None:
        sut = DummyHasLinks()
        expected: DumpMapping[Dump] = {
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
