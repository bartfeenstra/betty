import json
from pathlib import Path
from typing import Sequence, TYPE_CHECKING
import aiofiles
from betty.json.schema import (
    Schema,
    Ref,
    JsonSchemaReference,
    Array,
    JsonSchemaSchema,
    Def,
    FileBasedSchema,
    String,
    Integer,
    Number,
    Boolean,
    Object,
    Null,
    Const,
    Enum,
    AllOf,
    AnyOf,
    OneOf,
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

    def test_def_name_from___init__(self) -> None:
        def_name = "myFirstDefinition"
        sut = Schema(def_name=def_name)
        assert sut.def_name == def_name

    def test_title_from___init__(self) -> None:
        title = "My First Definition"
        sut = Schema(title=title)
        assert "title" in sut.schema
        assert sut.schema["title"] == title

    def test_description_from___init__(self) -> None:
        description = "My First Definition"
        sut = Schema(description=description)
        assert "description" in sut.schema
        assert sut.schema["description"] == description


class TestArray(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        schemas: MutableSequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]] = []
        for items_schema, valid_datas, invalid_datas in DUMMY_SCHEMAS:
            schemas.append(
                (
                    Array(items_schema),
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
                    Array(items_schema, def_name="myFirstArraySchema"),
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


class TestString(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(String(), ["", "abc"], [True, False, None, 123, [], {}])]


class TestNumber(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(Number(), [-123, 0, 123, 0.1, 9.9], [True, False, None, "", [], {}])]


class TestInteger(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                Integer(),
                [-123, 0, 123, 999],
                [True, False, None, "", 0.1, 9.9, [], {}],
            )
        ]


class TestBoolean(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(Boolean(), [True, False], [None, "", 123, [], {}])]


class TestObject(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(Object(), [{}], [None, "", 0.1, 9.9, []])]

    def test_add_property(self) -> None:
        sut = Object()
        property_name = "myFirstProperty"
        property_schema = Schema()
        sut.add_property(property_name, property_schema)
        assert sut.schema == {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                property_name: {},
            },
            "required": [property_name],
        }

    def test_add_property_with_optional(self) -> None:
        sut = Object()
        property_name = "myFirstProperty"
        property_schema = Null()
        sut.add_property(property_name, property_schema, False)
        assert sut.schema == {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                property_name: {"type": "null"},
            },
            "required": [],
        }


class TestConst(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (Const(True), [True], [False, None, "", 123, [], {}]),
            (Const("abc"), ["abc"], [True, False, None, "", 123, [], {}]),
        ]


class TestEnum(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                Enum(True, "abc", 123),
                [True, "abc", 123],
                [False, None, "", 456, [], {}],
            ),
        ]


class TestNull(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                Null(),
                [None],
                [True, False, "", 123, [], {}],
            )
        ]


class TestAllOf(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                AllOf(String(min_length=3), String(max_length=3)),
                ["abc"],
                [True, False, None, "ab", "abcd", 123, [], {}],
            )
        ]


class TestAnyOf(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            # "all of"-like behavior.
            (
                AnyOf(String(min_length=3), String(max_length=3)),
                ["ab", "abc", "abcd"],
                [True, False, None, 123, [], {}],
            ),
            # "one of"-like behavior.
            (
                AnyOf(String(), Integer()),
                ["abc", 123],
                [True, False, None, [], {}],
            ),
        ]


class TestOneOf(SchemaTestBase):
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                OneOf(String(), Integer()),
                ["abc", 123],
                [True, False, None, [], {}],
            )
        ]
