from typing import override

import pytest

from betty.json_schemas.openapi import OpenapiSchema
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut


class TestOpenapiSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (OpenapiSchema(), [], [])
