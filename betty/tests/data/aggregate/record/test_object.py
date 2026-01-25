from betty.data import Data
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import Attr, AttrDefinition, ObjectDefinition
from betty.data.bool import BoolDefinition
from betty.data.indicator.selector import Attr as AttrSelector
from betty.data.str import StrDefinition
from betty.locale.localizable.plain import Plain
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class ObjectDefinitionTestObject:
    def __init__(self, my_first_element: str):
        self.my_first_element = my_first_element


class ObjectDefinitionTestFactoryObject(ObjectDefinitionTestObject):
    pass


class TestObjectDefinition:
    def test_elements(self) -> None:
        element = FieldDefinition(
            AttrSelector("my_first_element"), StrDefinition(label=DUMMY_LOCALIZABLE)
        )
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label=DUMMY_LOCALIZABLE,
            fields=[element],
        )
        assert list(sut.fields) == [element]

    def test_load(self) -> None:
        field_name = "my_first_element"
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    AttrSelector(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            ],
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert data.my_first_element == value

    def test_load__with_factory(self) -> None:
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    AttrSelector("my_first_element"),
                    StrDefinition(label=DUMMY_LOCALIZABLE),
                ),
            ],
            factory=ObjectDefinitionTestFactoryObject,
        )
        assert isinstance(
            sut.load({"my_first_element": "Hello, world!"}),
            ObjectDefinitionTestFactoryObject,
        )

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = ObjectDefinition[ObjectDefinitionTestObject](
            cls=ObjectDefinitionTestObject,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    AttrSelector(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            ],
        )
        value = "Hello, world!"
        data = ObjectDefinitionTestObject(value)
        assert sut.dump(data) == {field_name: value}

    def test___call____without_attributes(self) -> None:
        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Object(Data[ObjectDefinition]):
            pass

        data_object = _Object.data()
        assert isinstance(data_object, ObjectDefinition)
        assert not data_object.fields

    def test___call____with_attr(self) -> None:
        class _Attr(Attr):
            @property
            def attr(self) -> AttrDefinition:
                return AttrDefinition(BoolDefinition(label=DUMMY_LOCALIZABLE))

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Object(Data[ObjectDefinition]):
            my_first_attr = _Attr()

        data_object = _Object.data()
        assert isinstance(data_object, ObjectDefinition)
        assert data_object.fields

    def test___call____with_attr_definition(self) -> None:
        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Object(Data[ObjectDefinition]):
            @property
            @AttrDefinition(BoolDefinition(label=DUMMY_LOCALIZABLE))
            def my_first_attr(self) -> bool:
                return True

        data_object = _Object.data()
        assert isinstance(data_object, ObjectDefinition)
        assert data_object.fields


class TestAttrDefinition:
    def test_field(self) -> None:
        name = "my_first_field"
        data = BoolDefinition(label=DUMMY_LOCALIZABLE)
        label = Plain("-")
        description = Plain("-")

        def empty(_):
            return False

        sut = AttrDefinition(
            data, label=label, description=description, empty=empty, optional=True
        )
        field = sut.field(name)
        assert field.selector.element == name
        assert field.data is data
        assert field.label is label
        assert field.description is description
        assert field.optional

    def test___call__(self) -> None:
        class _Object:
            @property
            @AttrDefinition(BoolDefinition(label=DUMMY_LOCALIZABLE))
            def my_first_attr(self) -> bool:
                return True

        assert _Object().my_first_attr
