from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.attrs.media_type import HasMediaType, MediaTypeAttr
from betty.media_type import MediaType, MediaTypeDefinition
from betty.plugins.media_type.plain_text import PLAIN_TEXT

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestMediaTypeAttr:
    def test_resolve(self) -> None:
        class Cls:
            media_type = MediaTypeAttr()

        instance = Cls()
        media_type = MediaType("text/plain")
        instance.media_type = MediaTypeDefinition("-", label="-", media_type=media_type)
        assert instance.media_type is media_type


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
