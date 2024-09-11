from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry.media_type import HasMediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.test_utils.json.linked_data import assert_dumps_linked_data

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump


class DummyHasMediaType(HasMediaType):
    pass


class TestHasMediaType:
    async def test_media_type(self) -> None:
        sut = DummyHasMediaType()
        assert sut.media_type is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                DummyHasMediaType(),
            ),
            (
                {
                    "mediaType": "text/plain",
                },
                DummyHasMediaType(media_type=PLAIN_TEXT),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: DummyHasMediaType
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
