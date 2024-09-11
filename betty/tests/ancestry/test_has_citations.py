from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.tests.ancestry.test_citation import DummyHasCitations

if TYPE_CHECKING:
    from betty.ancestry.link import HasLinks
    from betty.serde.dump import DumpMapping, Dump


class TestHasCitations:
    async def test_citations(self) -> None:
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
                    "id": "my-first-has-citations",
                    "citations": [],
                },
                DummyHasCitations(id="my-first-has-citations"),
            ),
            (
                {
                    "id": "my-first-has-citations",
                    "citations": [],
                },
                DummyHasCitations(
                    citations=[Citation(source=Source())], id="my-first-has-citations"
                ),
            ),
            (
                {
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
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
