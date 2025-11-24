import pytest
from typing_extensions import override

from betty.openapi.schema import SpecificationSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut


class TestSpecificationSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (SpecificationSchema(), [], [])
