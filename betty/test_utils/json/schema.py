"""
Test utilities for :py:mod:`betty.json.schema`.
"""

from collections.abc import Sequence, MutableMapping, Callable

import pytest
from betty.json.schema import Schema, JsonSchemaSchema, String
from betty.serde.dump import Dump
from jsonschema.exceptions import ValidationError

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

    @pytest.mark.parametrize(
        (
            "expected_def_name",
            "expected_title",
            "expected_description",
            "other_factory",
        ),
        [
            (None, None, None, Schema),
            (
                "myFirstDefinition",
                None,
                None,
                lambda: Schema(def_name="myFirstDefinition"),
            ),
            (
                None,
                "My First Definition",
                None,
                lambda: Schema(title="My First Definition"),
            ),
            (
                None,
                None,
                "My First Definition",
                lambda: Schema(description="My First Definition"),
            ),
        ],
    )
    async def test_wraps(
        self,
        expected_def_name: str | None,
        expected_title: str | None,
        expected_description: str | None,
        other_factory: Callable[[], Schema],
    ) -> None:
        """
        Tests :py:meth:`betty.json.schema.Schema.wraps` implementations.
        """
        for sut, _, __ in await self.get_sut_instances():
            other = other_factory()
            sut.wraps(other)
            if expected_def_name is not None:
                assert sut.def_name == expected_def_name
            if expected_title is not None:
                assert "title" in sut.schema
                assert sut.schema["title"] == expected_title
            if expected_description is not None:
                assert "description" in sut.schema
                assert sut.schema["description"] == expected_description
