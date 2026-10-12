from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from betty.media_types.html import HTML
from betty.media_types.plain_text import PLAIN_TEXT
from betty.validators.media_type import (
    UnsupportedFileType,
    UnsupportedMediaType,
    is_media_type,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.media_type import MediaType


class TestUnsupportedMediaType:
    def test_new(self) -> None:
        value = HTML.media_type
        sut = UnsupportedMediaType(value, [PLAIN_TEXT])
        assert sut.value is value
        assert str(PLAIN_TEXT.media_type) in str(sut)


class TestUnsupportedFileType:
    def test_new(self) -> None:
        value = Path()
        sut = UnsupportedFileType(value, [PLAIN_TEXT])
        assert sut.value is value
        assert str(PLAIN_TEXT.media_type) in str(sut)


@pytest.mark.parametrize(
    ("expected", "source", "media_types"),
    [
        (PLAIN_TEXT, PLAIN_TEXT, [PLAIN_TEXT]),
        (PLAIN_TEXT, PLAIN_TEXT, [HTML, PLAIN_TEXT]),
    ],
)
def test_is_media_type(
    expected: MediaType, source: MediaType, media_types: Iterable[MediaType]
) -> None:
    assert is_media_type(source, media_types=media_types) == expected


@pytest.mark.parametrize(
    ("source", "media_types"),
    [
        (PLAIN_TEXT, []),
        (PLAIN_TEXT, [HTML]),
    ],
)
def test_is_media_type__with_unsupported_media_type(
    source: MediaType, media_types: Iterable[MediaType]
) -> None:
    with pytest.raises(UnsupportedMediaType):
        is_media_type(source, media_types=media_types)
