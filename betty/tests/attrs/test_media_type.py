from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.attrs.media_type import Media, new_media_type_attr
from betty.media_type import MediaType, MediaTypeDefinition
from betty.media_types.plain_text import PLAIN_TEXT
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


class TestMedia:
    def test_media_type(self) -> None:
        sut = Media()
        assert sut.media_type is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                Media(),
            ),
            (
                {
                    "mediaType": "text/plain",
                },
                Media(media_type=PLAIN_TEXT),
            ),
        ],
    )
    async def test_dump_linked_data(
        self,
        assert_dumps_linked_data: AssertDumpsLinkedData,
        expected: PortableMapping,
        sut: Media,
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
