"""
Test utilities for :py:mod:`betty.json_schema`.
"""

from collections.abc import MutableMapping, Sequence

import pytest
from jsonschema.exceptions import ValidationError

from betty.json_schema import JsonSchemaSchema, Schema, String
from betty.portable import PortableData

DUMMY_SCHEMAS: Sequence[
    tuple[Schema, Sequence[PortableData], Sequence[PortableData]]
] = (
    (
        String(),
        [
            "",
            "Hello, world!",
        ],
        [True, False, None, 123, [], {}],
    ),
    (
        String(def_name="myFirstSchema"),
        ["", "Hello, world!"],
        [True, False, None, 123, [], {}],
    ),
)


type SchemaTestBaseSut = tuple[Schema, Sequence[PortableData], Sequence[PortableData]]


class SchemaTestBase:
    """
    A base class for testing :py:class:`betty.json_schema.Schema` implementations.
    """

    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    async def test_def_name(self, sut_data: SchemaTestBaseSut) -> None:
        """
        Tests :py:attr:`betty.json_schema.Schema.def_name` implementations.
        """
        sut, _, __ = sut_data
        assert sut.def_name is None or len(sut.def_name)

    async def test_schema(self, sut_data: SchemaTestBaseSut) -> None:
        """
        Tests :py:attr:`betty.json_schema.Schema.schema` implementations.
        """
        sut, _, __ = sut_data
        assert isinstance(sut.schema, MutableMapping)
        JsonSchemaSchema().validate(sut.schema)

    async def test_defs(self, sut_data: SchemaTestBaseSut) -> None:
        """
        Tests :py:attr:`betty.json_schema.Schema.defs` implementations.
        """
        sut, _, __ = sut_data
        assert isinstance(sut.defs, MutableMapping)

    async def test_embed(self, sut_data: SchemaTestBaseSut) -> None:
        """
        Tests :py:meth:`betty.json_schema.Schema.embed` implementations.
        """
        sut, _, __ = sut_data
        into = Schema()
        assert isinstance(sut.embed(into), MutableMapping)

    async def test_validate_should_validate(self, sut_data: SchemaTestBaseSut) -> None:
        """
        Tests :py:meth:`betty.json_schema.Schema.validate` implementations.
        """
        sut, valid_datas, _invalid_datas = sut_data
        for valid_data in valid_datas:
            sut.validate(valid_data)

    async def test_validate_should_invalidate(
        self, sut_data: SchemaTestBaseSut
    ) -> None:
        """
        Tests :py:meth:`betty.json_schema.Schema.validate` implementations.
        """
        sut, _valid_datas, invalid_datas = sut_data
        for invalid_data in invalid_datas:
            with pytest.raises(ValidationError):
                sut.validate(invalid_data)
