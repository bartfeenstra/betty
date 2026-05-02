from typing import override

import pytest

from betty.openapi.schema import SpecificationSchema
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut


class TestSpecificationSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (SpecificationSchema(), [], [])
