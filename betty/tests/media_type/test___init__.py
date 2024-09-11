from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.media_type import MediaType, MediaTypeSchema
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump
    from betty.json.schema import Schema


class TestMediaType:
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
        ],
    )
    async def test___str__(self, media_type: str) -> None:
        assert str(MediaType(media_type)) == media_type

    @pytest.mark.parametrize(
        ("expected", "media_type"),
        [
            ("plain", "text/plain"),
            ("form-data", "multipart/form-data"),
            ("vnd.oasis.opendocument.text", "application/vnd.oasis.opendocument.text"),
            ("ld", "application/ld+json"),
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
            (None, "text/plain"),
            (None, "multipart/form-data"),
            (None, "application/vnd.oasis.opendocument.text"),
            ("+json", "application/ld+json"),
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
        ],
    )
    async def test_type(
        self,
        expected: str,
        media_type: str,
    ) -> None:
        assert MediaType(media_type).type == expected

    def test_file_extensions(self) -> None:
        raise AssertionError

    def test_preferred_file_extension(self) -> None:
        raise AssertionError


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
                ],
                [True, False, None, 123, [], {}],
            ),
        ]
