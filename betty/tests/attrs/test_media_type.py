from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.attrs.media_type import HasMediaType, new_media_type_attr
from betty.media_type import MediaType, MediaTypeDefinition
from betty.plugins.media_type.plain_text import PLAIN_TEXT
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


def test_new_media_type_attr__set() -> None:
    class _Owner(HasProps):
        media_type = new_media_type_attr()

    owner = _Owner()
    media_type = MediaType("text/plain")
    owner.media_type = MediaTypeDefinition("-", label="-", media_type=media_type)
    assert owner.media_type is media_type


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
