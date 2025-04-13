"""
Test utilities for :py:mod:`betty.json.schema`.
"""

from collections.abc import MutableMapping, Sequence

import pytest
from jsonschema.exceptions import ValidationError

from betty.json.schema import JsonSchemaSchema, Schema, String
from betty.serde.dump import Dump

DUMMY_SCHEMAS: Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]] = (
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


class SchemaTestBase:
    """
    A base class for testing :py:class:`betty.json.schema.Schema` implementations.
    """

    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        """
        Get instances of the schema under test.

        :return: A tuple with the schema under test, a sequence of valid values, and a sequence of invalid values.
        """
        raise NotImplementedError

    async def test_def_name(self) -> None:
        """
        Tests :py:attr:`betty.json.schema.Schema.def_name` implementations.
        """
        for sut, _, __ in await self.get_sut_instances():
            assert sut.def_name is None or len(sut.def_name)

    async def test_schema(self) -> None:
        """
        Tests :py:attr:`betty.json.schema.Schema.schema` implementations.
        """
        for sut, _, __ in await self.get_sut_instances():
            assert isinstance(sut.schema, MutableMapping)
            (await JsonSchemaSchema.new()).validate(sut.schema)

    async def test_defs(self) -> None:
        """
        Tests :py:attr:`betty.json.schema.Schema.defs` implementations.
        """
        for sut, _, __ in await self.get_sut_instances():
            assert isinstance(sut.defs, MutableMapping)

    async def test_embed(self) -> None:
        """
        Tests :py:meth:`betty.json.schema.Schema.embed` implementations.
        """
        for sut, _, __ in await self.get_sut_instances():
            into = Schema()
            assert isinstance(sut.embed(into), MutableMapping)

    async def test_validate_should_validate(self) -> None:
        """
        Tests :py:meth:`betty.json.schema.Schema.validate` implementations.
        """
        for sut, valid_datas, _invalid_datas in await self.get_sut_instances():
            for valid_data in valid_datas:
                sut.validate(valid_data)

    async def test_validate_should_invalidate(self) -> None:
        """
        Tests :py:meth:`betty.json.schema.Schema.validate` implementations.
        """
        for sut, _valid_datas, invalid_datas in await self.get_sut_instances():
            for invalid_data in invalid_datas:
                with pytest.raises(ValidationError):
                    sut.validate(invalid_data)
