from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from jsonschema import ValidationError

from betty.json_schema.validate import validate
from betty.media_type import (
    MEDIA_TYPE_SCHEMA,
    InvalidMediaType,
    MediaType,
    MediaTypeDefinition,
    UnsupportedMediaType,
    match_extension,
    match_media_type,
    resolve_media_type,
)
from betty.plugins.media_type.html import HTML
from betty.plugins.media_type.plain_text import PLAIN_TEXT

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from betty.pathlib import StrPath


class TestMediaType:
    @pytest.mark.parametrize(
        (
            "expected_type",
            "expected_subtype",
            "expected_subtypes",
            "expected_suffix",
            "expected_parameters",
            "media_type",
        ),
        [
            # The simplest possible media type.
            ("text", "plain", ["plain"], None, {}, "text/plain"),
            # A media type with a hyphenated subtype.
            ("multipart", "form-data", ["form-data"], None, {}, "multipart/form-data"),
            # A media type with a tree subtype.
            (
                "application",
                "vnd.oasis.opendocument.text",
                ["vnd", "oasis", "opendocument", "text"],
                None,
                {},
                "application/vnd.oasis.opendocument.text",
            ),
            # A media type with a subtype suffix.
            ("application", "ld", ["ld"], "+json", {}, "application/ld+json"),
            # A media type with a parameter.
            (
                "text",
                "html",
                ["html"],
                None,
                {"charset": "UTF-8"},
                "text/html; charset=UTF-8",
            ),
        ],
    )
    def test(
        self,
        expected_type: str,
        expected_subtype: str,
        expected_subtypes: Sequence[str],
        expected_suffix: str | None,
        expected_parameters: Mapping[str, str],
        media_type: str,
    ) -> None:
        sut = MediaType(media_type)
        assert sut.type == expected_type
        assert sut.subtype == expected_subtype
        assert sut.subtypes == expected_subtypes
        assert sut.suffix == expected_suffix
        assert sut.parameters == expected_parameters
        assert str(sut) == media_type

    @pytest.mark.parametrize(
        "media_type",
        [
            "",
            "/",
            "text",
            "text/",
            "foo",
            "bar",
        ],
    )
    def test_invalid_type_should_raise_error(self, media_type: str) -> None:
        with pytest.raises(InvalidMediaType):
            MediaType(media_type)

    @pytest.mark.parametrize(
        ("expected", "left", "right"),
        [
            (True, MediaType("text/plain"), MediaType("text/plain")),
            (
                True,
                MediaType("text/plain"),
                MediaTypeDefinition("-", label="-", media_type=MediaType("text/plain")),
            ),
            (True, MediaType("text/plain"), "text/plain"),
            (False, MediaType("text/plain"), "text/html"),
            (True, MediaType("multipart/form-data"), "multipart/form-data"),
            (
                True,
                MediaType("application/vnd.oasis.opendocument.text"),
                "application/vnd.oasis.opendocument.text",
            ),
            (
                False,
                MediaType("application/vnd.oasis.opendocument.text"),
                "application/vnd.oasis.opendocument.presentation",
            ),
            (True, MediaType("text/html; charset=UTF-8"), "text/html; charset=UTF-8"),
            (False, MediaType("text/html; charset=UTF-8"), "text/html; charset=UTF-16"),
        ],
    )
    def test___eq__(
        self, expected: bool, left: MediaType, right: MediaType | str
    ) -> None:
        assert (left == right) == expected

    @pytest.mark.parametrize(
        "other",
        [True, False, None, "abc", 123, [], {}],
    )
    def test___eq___with_not_implemented(self, other: Any) -> None:
        assert other != PLAIN_TEXT

    @pytest.mark.parametrize(
        ("expected", "left", "right"),
        [
            (True, "text/plain", "text/plain"),
            (False, "text/plain", "text/html"),
            (True, "multipart/form-data", "multipart/form-data"),
            (
                True,
                "application/vnd.oasis.opendocument.text",
                "application/vnd.oasis.opendocument.text",
            ),
            (
                False,
                "application/vnd.oasis.opendocument.text",
                "application/vnd.oasis.opendocument.presentation",
            ),
            (True, "text/html; charset=UTF-8", "text/html; charset=UTF-8"),
            (False, "text/html; charset=UTF-8", "text/html; charset=UTF-16"),
        ],
    )
    def test___hash__(self, expected: bool, left: str, right: str) -> None:
        assert (hash(MediaType(left)) == hash(MediaType(right))) == expected

    @pytest.mark.parametrize(
        "media_type",
        [
            "text/plain",
            "multipart/form-data",
            "application/vnd.oasis.opendocument.text",
            "application/ld+json",
            "text/html; charset=UTF-8",
        ],
    )
    def test___str__(self, media_type: str) -> None:
        assert str(MediaType(media_type)) == media_type

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            ({}, "text/plain"),
            ({}, "multipart/form-data"),
            ({}, "application/vnd.oasis.opendocument.text"),
            ({}, "application/ld+json"),
            ({"charset": "UTF-8"}, "text/html; charset=UTF-8"),
        ],
    )
    def test_parameters(
        self,
        expected: Mapping[str, str],
        media_type: str,
    ) -> None:
        assert MediaType(media_type).parameters == expected

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            ("plain", "text/plain"),
            ("form-data", "multipart/form-data"),
            ("vnd.oasis.opendocument.text", "application/vnd.oasis.opendocument.text"),
            ("ld", "application/ld+json"),
            ("html", "text/html; charset=UTF-8"),
        ],
    )
    def test_subtype(
        self,
        expected: str,
        media_type: str,
    ) -> None:
        assert MediaType(media_type).subtype == expected

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            (["plain"], "text/plain"),
            (["form-data"], "multipart/form-data"),
            (
                ["vnd", "oasis", "opendocument", "text"],
                "application/vnd.oasis.opendocument.text",
            ),
            (["ld"], "application/ld+json"),
            (["html"], "text/html; charset=UTF-8"),
        ],
    )
    def test_subtypes(
        self,
        expected: Sequence[str],
        media_type: str,
    ) -> None:
        assert MediaType(media_type).subtypes == expected

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            (None, "text/plain"),
            (None, "multipart/form-data"),
            (None, "application/vnd.oasis.opendocument.text"),
            ("+json", "application/ld+json"),
            (None, "text/html; charset=UTF-8"),
        ],
    )
    def test_suffix(
        self,
        expected: str | None,
        media_type: str,
    ) -> None:
        assert MediaType(media_type).suffix == expected

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            ("text", "text/plain"),
            ("multipart", "multipart/form-data"),
            ("application", "application/vnd.oasis.opendocument.text"),
            ("application", "application/ld+json"),
            ("text", "text/html; charset=UTF-8"),
        ],
    )
    def test_type(
        self,
        expected: str,
        media_type: str,
    ) -> None:
        assert MediaType(media_type).type == expected

    def test_extensions(self) -> None:
        extensions = [".one", ".two", ".three"]
        sut = MediaType("text/plain", extensions=extensions)
        assert sut.extensions == extensions

    def test_load(self) -> None:
        assert MediaType.load("application/vnd.oasis.opendocument.text") == MediaType(
            "application/vnd.oasis.opendocument.text"
        )

    def test_dump(self) -> None:
        assert (
            MediaType("application/vnd.oasis.opendocument.text").dump()
            == "application/vnd.oasis.opendocument.text"
        )


@pytest.mark.parametrize(
    ("expected", "source", "media_types"),
    [
        (PLAIN_TEXT, PLAIN_TEXT, [PLAIN_TEXT]),
        (PLAIN_TEXT, PLAIN_TEXT, [HTML, PLAIN_TEXT]),
    ],
)
def test_match_media_type(
    expected: MediaType, source: MediaType, media_types: Iterable[MediaType]
) -> None:
    assert match_media_type(source, media_types) == expected


@pytest.mark.parametrize(
    ("source", "media_types"),
    [
        (PLAIN_TEXT, []),
        (PLAIN_TEXT, [HTML]),
    ],
)
def test_match_media_type__with_unsupported_media_type(
    source: MediaType, media_types: Iterable[MediaType]
) -> None:
    with pytest.raises(UnsupportedMediaType):
        match_media_type(source, media_types)


@pytest.mark.parametrize(
    ("expected", "source", "media_types"),
    [
        ((PLAIN_TEXT, ".txt"), "my.first.source.txt", [PLAIN_TEXT.media_type]),
        ((PLAIN_TEXT, ".txt"), Path("my.first.source.txt"), [PLAIN_TEXT.media_type]),
        (
            (PLAIN_TEXT, ".txt"),
            "my.first.source.txt",
            [HTML.media_type, PLAIN_TEXT.media_type],
        ),
    ],
)
def test_match_extension(
    expected: tuple[MediaType, str],
    source: StrPath,
    media_types: Iterable[MediaType],
) -> None:
    assert match_extension(source, media_types) == expected


@pytest.mark.parametrize(
    ("source", "media_types"),
    [
        ("my.first.source.txt", []),
        ("", [PLAIN_TEXT.media_type]),
        ("my.first.source.txt", [HTML.media_type]),
    ],
)
def test_match_extension__with_unsupported_media_type(
    source: StrPath, media_types: Iterable[MediaType]
) -> None:
    with pytest.raises(UnsupportedMediaType):
        match_extension(source, media_types)


class TestUnsupportedMediaType:
    def test_new(self) -> None:
        sut = UnsupportedMediaType(PLAIN_TEXT.media_type)
        assert str(PLAIN_TEXT.media_type) in str(sut)


class TestMediaTypeDefinition:
    def test_media_type(self) -> None:
        media_type = MediaType("text/plain")
        assert (
            MediaTypeDefinition("-", label="-", media_type=media_type).media_type
            is media_type
        )


def test_resolve_media_type__with_media_type() -> None:
    media_type = MediaType("text/plain")
    assert resolve_media_type(media_type) is media_type


def test_resolve_media_type__with_media_type_definition() -> None:
    media_type = MediaType("text/plain")
    assert (
        resolve_media_type(MediaTypeDefinition("-", label="-", media_type=media_type))
        is media_type
    )


@pytest.mark.parametrize(
    "value",
    [
        "text/plain",
        "multipart/form-data",
        "application/vnd.oasis.opendocument.text",
        "application/ld+json",
        "text/html; charset=UTF-8",
    ],
)
def test_media_type_schema__with_valid_value(value: str) -> None:
    validate(MEDIA_TYPE_SCHEMA, value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        None,
        123,
        [],
        {},
    ],
)
def test_media_type_schema__with_invalid_value(value: str) -> None:
    with pytest.raises(ValidationError):
        validate(MEDIA_TYPE_SCHEMA, value)
