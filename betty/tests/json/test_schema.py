import json
from pathlib import Path
from typing import Sequence, TYPE_CHECKING
import aiofiles
from betty.json.schema import (
    Schema,
    Ref,
    JsonSchemaReference,
    ArraySchema,
    JsonSchemaSchema,
    Def,
    FileBasedSchema,
)
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase, DUMMY_SCHEMAS
from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import MutableSequence


class TestSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return DUMMY_SCHEMAS

    def test_name_with_name(self) -> None:
        name = "myFirstSchema"
        sut = Schema(def_name=name)
        assert sut.def_name == name

    def test_name_without_name(self) -> None:
        sut = Schema()
        assert sut.def_name is None


class TestArraySchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        schemas: MutableSequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]] = []
        for items_schema, valid_datas, invalid_datas in DUMMY_SCHEMAS:
            schemas.append(
                (
                    ArraySchema(items_schema),
                    [*[[data] for data in valid_datas], list(valid_datas)],
                    [
                        True,
                        False,
                        None,
                        123,
                        "abc",
                        {},
                        *[[invalid_data] for invalid_data in invalid_datas],
                    ],
                )
            )
            schemas.append(
                (
                    ArraySchema(items_schema, def_name="myFirstArraySchema"),
                    [*[[data] for data in valid_datas], list(valid_datas)],
                    [
                        True,
                        False,
                        None,
                        123,
                        "abc",
                        {},
                        *[[invalid_data] for invalid_data in invalid_datas],
                    ],
                )
            )
        return schemas


class TestDef:
    def test(self) -> None:
        sut = Def("myFirstSchema")
        assert sut == "#/$defs/myFirstSchema"


class TestRef(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (Ref("someDefinition"), [], []),
        ]


class TestFileBasedSchema:
    async def test_new_for(self, tmp_path: Path) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "string",
        }
        schema_path = tmp_path / "schema.json"
        async with aiofiles.open(schema_path, "w") as f:
            await f.write(json.dumps(schema))
        sut = await FileBasedSchema.new_for(schema_path)
        assert sut.schema == schema


class TestJsonSchemaReference(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                JsonSchemaReference(),
                ["https://json-schema.org/draft/2020-12/schema"],
                [True, False, None, 123, [], {}],
            )
        ]


class TestJsonSchemaSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(await JsonSchemaSchema.new(), [], [])]
