from __future__ import annotations

from betty.attrs.content_type import HasContentType, new_content_type_attr
from betty.classtools.init import Init
from betty.content_type import ContentTypeDefinition
from betty.content_types import plain_text


def test_new_content_type_attr__set() -> None:
    class _Owner(Init):
        media_type = new_content_type_attr()

    owner = _Owner()
    owner.media_type = ContentTypeDefinition(
        "-", label="-", media_type=plain_text.media_type
    )
    assert owner.media_type is plain_text


class TestHasContentType:
    def test_content_type(self) -> None:
        sut = HasContentType()
        assert sut.content_type is None
