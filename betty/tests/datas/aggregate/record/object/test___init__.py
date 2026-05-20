from dataclasses import dataclass

from betty.data import Data
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Attr as AttrSelector
from betty.locale.localizable.plain import Plain


@dataclass(frozen=True)
class ObjectDefinitionTestObject:
    my_first_element: str


@dataclass(frozen=True)
class ObjectDefinitionTestFactoryObject(ObjectDefinitionTestObject):
    pass


class TestObjectDefinition:
    def test_load(self) -> None:
        field_name = "my_first_element"
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label="-",
            fields={
                AttrSelector(field_name): FieldDefinition(StrDefinition(label="-")),
            },
        )
        value = "Hello, world!"
        data = sut.porter.load({field_name: value})
        assert data.my_first_element == value

    def test_load__with_factory(self) -> None:
        field_name = "my_first_element"
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label="-",
            fields={
                AttrSelector(field_name): FieldDefinition(StrDefinition(label="-")),
            },
            factory=ObjectDefinitionTestFactoryObject,
        )
        assert isinstance(
            sut.porter.load({"my_first_element": "Hello, world!"}),
            ObjectDefinitionTestFactoryObject,
        )

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label="-",
            fields={
                AttrSelector(field_name): FieldDefinition(StrDefinition(label="-")),
            },
        )
        value = "Hello, world!"
        data = ObjectDefinitionTestObject(value)
        assert sut.porter.dump(data) == {field_name: value}

    def test__set_cls__without_attributes(self) -> None:
        @ObjectDefinition(label="-")
        class _Object(Data[ObjectDefinition]):
            pass

        data_object = _Object.data()
        assert isinstance(data_object, ObjectDefinition)
        assert not data_object.fields


class TestFieldDefinition:
    def test_data(self) -> None:
        data = BoolDefinition(label="-")
        sut = FieldDefinition(data)
        assert sut.data is data

    def test_label(self) -> None:
        label = Plain("-")
        sut = FieldDefinition(BoolDefinition(label="-"), label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("-")
        sut = FieldDefinition(BoolDefinition(label="-"), description=description)
        assert sut.description is description

    def test_omit_load(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_load=True)
        assert sut.omit_load

    def test_omit_dump(self) -> None:
        def _omit_dump(_: bool) -> bool:
            return True

        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=_omit_dump)
        assert sut.omit_dump(object(), False)
