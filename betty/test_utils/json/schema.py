"""
Test utilities for :py:mod:`betty.json.schema`.
"""

from collections.abc import Sequence, MutableMapping

from betty.json.schema import Schema, JsonSchemaSchema
from betty.serde.dump import Dump

DUMMY_SCHEMAS: Sequence[tuple[Schema, Sequence[Dump]]] = (
    (Schema(), ()),
    (Schema(name="myFirstSchema"), ()),
    (Schema(schema={}), ()),
    (
        Schema(
            schema={
                "type": "string",
            }
        ),
        (
            "",
            "Hello, world!",
        ),
    ),
    (
        Schema(
            name="myFirstSchema",
            schema={
                "type": "string",
            },
        ),
        ("", "Hello, world!"),
    ),
)


class SchemaTestBase:
    """
    A base class for testing :py:class:`betty.json.schema.Schema` implementations.
    """

    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        """
        Get instances of the schema under test.
        """
        raise NotImplementedError

    async def test_schema(self) -> None:
        """
        Tests :py:attr:`betty.json.schema.Schema.schema` implementations.
        """
        for sut, _ in await self.get_sut_instances():
            assert isinstance(sut.schema, MutableMapping)
            (await JsonSchemaSchema.new()).validate(sut.schema)

    async def test_definitions(self) -> None:
        """
        Tests :py:attr:`betty.json.schema.Schema.definitions` implementations.
        """
        for sut, _ in await self.get_sut_instances():
            assert isinstance(sut.schema, MutableMapping)

    async def test_embed(self) -> None:
        """
        Tests :py:meth:`betty.json.schema.Schema.embed` implementations.
        """
        for sut, _ in await self.get_sut_instances():
            into = Schema()
            assert isinstance(sut.embed(into), MutableMapping)

    async def test_validate(self) -> None:
        """
        Tests :py:meth:`betty.json.schema.Schema.validate` implementations.
        """
        for sut, datas in await self.get_sut_instances():
            for data in datas:
                sut.schema["$id"] = "betty"
                sut.validate(data)
