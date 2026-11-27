from __future__ import annotations

from betty.content_type import (
    ContentTypeDefinition,
    MissingContentType,
    UnsupportedContentType,
)
from betty.content_types import plain_text
from betty.media_type import MediaType


class TestUnsupportedContentType:
    def test_new(self) -> None:
        sut = UnsupportedContentType(plain_text.media_type)
        assert str(plain_text.media_type) in str(sut)


class TestMissingContentType:
    def test_new(self) -> None:
        assert str(MissingContentType())


class TestContentTypeDefinition:
    def test_media_type(self) -> None:
        media_type = MediaType("text/plain")
        assert (
            ContentTypeDefinition("-", label="-", media_type=media_type).media_type
            is media_type
        )

    def test_extensions(self) -> None:
        extension = (".one", ".two", ".three")
        sut = ContentTypeDefinition(
            "-", label="-", media_type="text/plain", extension=extension
        )
        assert list(sut.extensions) == extension
