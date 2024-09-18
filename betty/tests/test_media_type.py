from __future__ import annotations

from typing import Sequence, TYPE_CHECKING, Any

import pytest
from typing_extensions import override

from betty.media_type import MediaType, InvalidMediaType, MediaTypeSchema, PLAIN_TEXT
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.serde.dump import Dump
    from betty.json.schema import Schema


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
    async def test(
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
    async def test_invalid_type_should_raise_error(self, media_type: str) -> None:
        with pytest.raises(InvalidMediaType):
            MediaType(media_type)

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
    async def test___eq__(self, expected: bool, left: str, right: str) -> None:
        assert (MediaType(left) == MediaType(right)) == expected

    @pytest.mark.parametrize(
        "other",
        [True, False, None, "abc", 123, [], {}],
    )
    async def test___eq___with_not_implemented(self, other: Any) -> None:
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
    async def test___hash__(self, expected: bool, left: str, right: str) -> None:
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
    async def test___str__(self, media_type: str) -> None:
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
    async def test_parameters(
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
    async def test_subtype(
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
    async def test_subtypes(
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
    async def test_suffix(
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
    async def test_type(
        self,
        expected: str,
        media_type: str,
    ) -> None:
        assert MediaType(media_type).type == expected


class TestMediaTypeSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                MediaTypeSchema(),
                [
                    "text/plain",
                    "multipart/form-data",
                    "application/vnd.oasis.opendocument.text",
                    "application/ld+json",
                    "text/html; charset=UTF-8",
                ],
                [True, False, None, 123, [], {}],
            ),
        ]
