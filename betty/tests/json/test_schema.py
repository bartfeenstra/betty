from collections.abc import Sequence
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.json.schema import (
    AllOf,
    AnyOf,
    Array,
    Boolean,
    Const,
    Def,
    Enum,
    Integer,
    JsonSchemaReference,
    JsonSchemaSchema,
    Null,
    Number,
    Object,
    OneOf,
    Ref,
    Schema,
    String,
)
from betty.serde.dump import Dump
from betty.test_utils.json.schema import DUMMY_SCHEMAS, SchemaTestBase

if TYPE_CHECKING:
    from collections.abc import MutableSequence


class TestSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return DUMMY_SCHEMAS

    def test_def_name__from___init__(self) -> None:
        def_name = "myFirstDefinition"
        sut = Schema(def_name=def_name)
        assert sut.def_name == def_name

    def test___init___with_title(self) -> None:
        title = "My First Definition"
        sut = Schema(title=title)
        assert "title" in sut.schema
        assert sut.title == title

    def test___init___with_description(self) -> None:
        description = "My First Definition"
        sut = Schema(description=description)
        assert "description" in sut.schema
        assert sut.description == description

    def test_title(self) -> None:
        title = "My First Definition"
        sut = Schema()
        sut.title = title
        assert sut.title == title

    def test_title__default(self) -> None:
        sut = Schema()
        assert sut.title is None

    def test_description(self) -> None:
        description = "My First Definition"
        sut = Schema()
        sut.description = description
        assert sut.description == description

    def test_description__default(self) -> None:
        sut = Schema()
        assert sut.description is None


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
        return [(JsonSchemaSchema(), [], [])]


class TestString(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(String(), ["", "abc"], [True, False, None, 123, [], {}])]


class TestNumber(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(Number(), [-123, 0, 123, 0.1, 9.9], [True, False, None, "", [], {}])]


class TestInteger(SchemaTestBase):
    @override
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
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(Boolean(), [True, False], [None, "", 123, [], {}])]


class TestObject(SchemaTestBase):
    @override
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

    def test_add_property__with_optional(self) -> None:
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
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (Const(True), [True], [False, None, "", 123, [], {}]),
            (Const("abc"), ["abc"], [True, False, None, "", 123, [], {}]),
        ]


class TestEnum(SchemaTestBase):
    @override
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
    @override
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
    @override
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
    @override
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
    @override
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
