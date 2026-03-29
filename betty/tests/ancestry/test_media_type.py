from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry.media_type import HasMediaType
from betty.media_type.media_types import PLAIN_TEXT

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestHasMediaType:
    def test_media_type(self) -> None:
        sut = HasMediaType()
        assert sut.media_type is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                HasMediaType(),
            ),
            (
                {
                    "mediaType": "text/plain",
                },
                HasMediaType(media_type=PLAIN_TEXT),
            ),
        ],
    )
    async def test_dump_linked_data(
        self,
        assert_dumps_linked_data: AssertDumpsLinkedData,
        expected: PortableMapping,
        sut: HasMediaType,
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
