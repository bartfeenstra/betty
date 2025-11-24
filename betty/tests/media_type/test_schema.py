from __future__ import annotations

import pytest
from typing_extensions import override

from betty.media_type.schema import MediaTypeSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut


class TestMediaTypeSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            MediaTypeSchema(),
            [
                "text/plain",
                "multipart/form-data",
                "application/vnd.oasis.opendocument.text",
                "application/ld+json",
                "text/html; charset=UTF-8",
            ],
            [True, False, None, 123, [], {}],
        )
