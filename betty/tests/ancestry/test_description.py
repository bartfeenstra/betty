from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.test_utils.ancestry.description import DummyHasDescription
from betty.test_utils.json.linked_data import assert_dumps_linked_data

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.ancestry.link import HasLinks


class TestHasDescription:
    async def test_description(self) -> None:
        sut = DummyHasDescription()
        assert not sut.description

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                DummyHasDescription(),
            ),
            (
                {
                    "@context": {"description": "https://schema.org/description"},
                    "description": {"translations": {"und": "Hello, world!"}},
                },
                DummyHasDescription(description="Hello, world!"),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
