from __future__ import annotations

from typing import override

import pytest

from betty.media_type.schema import MediaTypeSchema
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut


class TestMediaTypeSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
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
