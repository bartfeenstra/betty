from typing import override

import pytest

from betty.json_schemas.json_schema import JsonSchemaSchema
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut


class TestJsonSchemaSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (JsonSchemaSchema(), [], [])
