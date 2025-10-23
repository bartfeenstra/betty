from collections.abc import Iterable, Sequence
from typing import cast

import pytest
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
from betty.test_utils.json.schema import (
    DUMMY_SCHEMAS,
    SchemaTestBase,
    SchemaTestBaseSut,
)


class TestSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Sequence[SchemaTestBaseSut]:
        return DUMMY_SCHEMAS

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)

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
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        for items_schema, valid_datas, invalid_datas in DUMMY_SCHEMAS:
            yield (
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
            yield (
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

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestDef:
    def test(self) -> None:
        sut = Def("myFirstSchema")
        assert sut == "#/$defs/myFirstSchema"


class TestRef(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (Ref("someDefinition"), [], [])


class TestJsonSchemaReference(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            JsonSchemaReference(),
            ["https://json-schema.org/draft/2020-12/schema"],
            [True, False, None, 123, [], {}],
        )


class TestJsonSchemaSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (JsonSchemaSchema(), [], [])


class TestString(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (String(), ["", "abc"], [True, False, None, 123, [], {}])


class TestNumber(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (Number(), [-123, 0, 123, 0.1, 9.9], [True, False, None, "", [], {}])


class TestInteger(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            Integer(),
            [-123, 0, 123, 999],
            [True, False, None, "", 0.1, 9.9, [], {}],
        )


class TestBoolean(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (Boolean(), [True, False], [None, "", 123, [], {}])


class TestObject(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (Object(), [{}], [None, "", 0.1, 9.9, []])

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
    @staticmethod
    def _sut_params() -> Sequence[SchemaTestBaseSut]:
        return [
            (Const(True), [True], [False, None, "", 123, [], {}]),
            (Const("abc"), ["abc"], [True, False, None, "", 123, [], {}]),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestEnum(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            Enum(True, "abc", 123),
            [True, "abc", 123],
            [False, None, "", 456, [], {}],
        )


class TestNull(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            Null(),
            [None],
            [True, False, "", 123, [], {}],
        )


class TestAllOf(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            AllOf(String(min_length=3), String(max_length=3)),
            ["abc"],
            [True, False, None, "ab", "abcd", 123, [], {}],
        )


class TestAnyOf(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Sequence[SchemaTestBaseSut]:
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

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestOneOf(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            OneOf(String(), Integer()),
            ["abc", 123],
            [True, False, None, [], {}],
        )
