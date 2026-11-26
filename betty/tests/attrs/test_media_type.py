from __future__ import annotations

from betty.attrs.media_type import HasMediaType, new_media_type_attr
from betty.classtools.init import Init
from betty.content_type import ContentTypeDefinition
from betty.media_types import plain_text


def test_new_media_type_attr__set() -> None:
    class _Owner(Init):
        media_type = new_media_type_attr()

    owner = _Owner()
    owner.media_type = ContentTypeDefinition(
        "-", label="-", media_type=plain_text.media_type
    )
    assert owner.media_type is plain_text


class TestHasMediaType:
    def test_media_type(self) -> None:
        sut = HasMediaType()
        assert sut.media_type is None
