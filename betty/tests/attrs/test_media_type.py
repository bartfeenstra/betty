from __future__ import annotations

from betty.attrs.media_type import HasMediaType, new_media_type_attr
from betty.classtools.init import Init
from betty.media_type import MediaType, MediaTypeDefinition


def test_new_media_type_attr__set() -> None:
    class _Owner(Init):
        media_type = new_media_type_attr()

    owner = _Owner()
    media_type = MediaType("text/plain")
    owner.media_type = MediaTypeDefinition("-", label="-", media_type=media_type)
    assert owner.media_type is media_type


class TestHasMediaType:
    def test_media_type(self) -> None:
        sut = HasMediaType()
        assert sut.media_type is None
