from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.plugins.entity.citation import Citation
from betty.plugins.entity.source import Source
from betty.test_utils.ancestry.has_citations import DummyHasCitations

if TYPE_CHECKING:
    from betty.entity.has_links import HasLinks
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestHasCitations:
    def test___init___with_citations(self) -> None:
        citation = Citation(source=Source())
        sut = DummyHasCitations(citations=[citation])
        assert list(sut.citations) == [citation]

    def test_citations(self) -> None:
        sut = DummyHasCitations()
        assert list(sut.citations) == []
        citation = Citation(source=Source())
        sut.citations = [citation]
        assert list(sut.citations) == [citation]

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@id": "https://example.com/dummy-has-citations/my-first-has-citations/index.json",
                    "id": "my-first-has-citations",
                    "citations": [],
                },
                DummyHasCitations(id="my-first-has-citations"),
            ),
            (
                {
                    "@id": "https://example.com/dummy-has-citations/my-first-has-citations/index.json",
                    "id": "my-first-has-citations",
                    "citations": [],
                },
                DummyHasCitations(
                    citations=[Citation(source=Source())], id="my-first-has-citations"
                ),
            ),
            (
                {
                    "@id": "https://example.com/dummy-has-citations/my-first-has-citations/index.json",
                    "id": "my-first-has-citations",
                    "citations": ["/citation/my-first-citation/index.json"],
                },
                DummyHasCitations(
                    citations=[Citation(source=Source(), id="my-first-citation")],
                    id="my-first-has-citations",
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self,
        assert_dumps_linked_data: AssertDumpsLinkedData,
        expected: PortableMapping,
        sut: HasLinks,
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
