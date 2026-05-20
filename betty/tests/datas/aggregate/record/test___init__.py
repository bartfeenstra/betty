from dataclasses import dataclass
from typing import Self, override
from unittest.mock import Mock

import pytest

from betty.data import DataDefinition
from betty.datas.aggregate.record import (
    FieldDefinition,
    MappingPorter,
    PortableRecord,
    PortableRecordPorter,
    RecordDefinition,
    RecordPorter,
)
from betty.datas.bool import BoolDefinition
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.exception import HumanFacingException
from betty.indicator.selector import Attr
from betty.locale.localizable.plain import Plain
from betty.portable import PortableData


class TestFieldDefinition:
    def test_omit_load(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"))
        assert not sut.omit_load

    def test_omit_load__with_omit_load(self) -> None:
        sut = FieldDefinition(
            BoolDefinition(label="-"),
            omit_load=True,
        )
        assert sut.omit_load

    def test_omit_load__with_optional_definition(self) -> None:
        sut = FieldDefinition(
            OptionalDefinition(BoolDefinition(label="-")), omit_load=True
        )
        assert sut.omit_load

    def test_omit_dump__with_callable_false(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=lambda _: False)
        assert not sut.omit_dump(object(), True)

    def test_omit_dump__with_callable_true(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=lambda _: True)
        assert sut.omit_dump(object(), True)

    def test_omit_dump__with_none(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=None)
        assert not sut.omit_dump(object(), True)

    def test_data(self) -> None:
        data = DataDefinition(label="-")
        sut = FieldDefinition(data)
        assert sut.data is data

    def test_label__with_label(self) -> None:
        label = Plain("-")
        sut = FieldDefinition(DataDefinition(label="-"), label=label)
        assert sut.label is label

    def test_description__without_description(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"))
        assert sut.description is None

    def test_description__with_description(self) -> None:
        description = Plain("-")
        sut = FieldDefinition(DataDefinition(label="-"), description=description)
        assert sut.description is description

    def test_omit__without_callback(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"))
        assert not sut.omit_dump(object(), object())

    def test_omit__with_callback(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"), omit_dump=lambda _: True)
        assert sut.omit_dump(object(), object())


@dataclass(frozen=True)
class RecordDefinitionTestRecord:
    my_first_element: str | None = None


@dataclass(frozen=True)
class RecordDefinitionTestFactoryRecord(RecordDefinitionTestRecord):
    pass


class TestRecordDefinition:
    def test_factory__without_factory(self) -> None:
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord, label="-"
        )
        assert sut.factory is RecordDefinitionTestRecord

    def test_factory__with_factory(self) -> None:
        def factory() -> RecordDefinitionTestRecord:
            return RecordDefinitionTestRecord()

        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord, label="-", factory=factory
        )
        assert sut.factory is factory

    def test_porter__without_porter(self) -> None:
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord, label="-"
        )
        assert isinstance(sut.porter, MappingPorter)

    def test_porter__with_porter(self) -> None:
        m_porter = Mock(spec=RecordPorter)
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord, label="-", porter=m_porter
        )
        assert sut.porter is m_porter

    def test_fields(self) -> None:
        field = FieldDefinition(StrDefinition(label="-"))
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label="-",
            fields={Attr("my_first_element"): field},
        )
        assert dict(sut.fields) == {Attr("my_first_element"): field}


class TestMappingPorter:
    def test_load__with_value(self) -> None:
        field_name = "my_first_element"
        sut = MappingPorter(
            RecordDefinition[RecordDefinitionTestRecord, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert data.my_first_element == value

    def test_load__without_value(self) -> None:
        field_name = "my_first_element"
        sut = MappingPorter(
            RecordDefinition[RecordDefinitionTestRecord, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        with pytest.raises(HumanFacingException):
            sut.load({})

    def test_load__with_factory(self) -> None:
        field_name = "my_first_element"
        sut = MappingPorter(
            RecordDefinition[RecordDefinitionTestRecord, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
                factory=RecordDefinitionTestFactoryRecord,
            )
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert isinstance(data, RecordDefinitionTestFactoryRecord)
        assert data.my_first_element == value

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = MappingPorter(
            RecordDefinition[RecordDefinitionTestRecord, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        value = "Hello, world!"
        data = RecordDefinitionTestRecord(value)
        assert sut.dump(data) == {field_name: value}

    def test_load_key(self) -> None:
        field_name = "my_first_element"
        sut = MappingPorter(
            RecordDefinition[RecordDefinitionTestRecord, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        value = "Hello, world!"
        data = sut.load_key({}, Attr(field_name), value)
        assert data.my_first_element == value

    def test_dump_key(self) -> None:
        field_name = "my_first_element"
        sut = MappingPorter(
            RecordDefinition[RecordDefinitionTestRecord, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        value = "Hello, world!"
        data = RecordDefinitionTestRecord(value)
        assert sut.dump_key(data, Attr(field_name)) == (value, {})


class PortableRecordPorterTestPortableRecord(PortableRecord[Attr]):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        raise NotImplementedError

    @override
    def dump(self) -> PortableData:
        raise NotImplementedError

    @override
    @classmethod
    def load_key(cls, portable: PortableData, key: Attr, portable_key: str, /) -> Self:
        return cls(portable_key, portable["value"])  # ty:ignore[invalid-argument-type, not-subscriptable]

    @override
    def dump_key(self, key: Attr, /) -> tuple[str, PortableData]:
        return self.key, {"value": self.value}  # ty:ignore[invalid-return-type]


class TestPortableRecordPorter:
    def test_load_key(self) -> None:
        sut = PortableRecordPorter(PortableRecordPorterTestPortableRecord)
        key = "hello-world"
        value = "Hello, world!"
        data = sut.load_key({"value": value}, Attr("key"), key)
        assert data.key == key
        assert data.value == value

    def test_dump_key(self) -> None:
        sut = PortableRecordPorter(PortableRecordPorterTestPortableRecord)
        key = "hello-world"
        value = "Hello, world!"
        data = PortableRecordPorterTestPortableRecord(key, value)
        assert sut.dump_key(data, Attr("key")) == (key, {"value": value})
