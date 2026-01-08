from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.data.simple import SimpleDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class ObjectDefinitionTestObject:
    def __init__(self, my_first_element: str):
        self.my_first_element = my_first_element


class ObjectDefinitionTestFactoryObject(ObjectDefinitionTestObject):
    pass


class TestObjectDefinition:
    def test_elements(self) -> None:
        element = FieldDefinition(
            Attr("my_first_element"), SimpleDefinition(cls=str, label=DUMMY_LOCALIZABLE)
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
                    Attr(field_name),
                    SimpleDefinition(cls=str, label=DUMMY_LOCALIZABLE),
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
                    Attr("my_first_element"),
                    SimpleDefinition(cls=str, label=DUMMY_LOCALIZABLE),
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
                    Attr(field_name),
                    SimpleDefinition(cls=str, label=DUMMY_LOCALIZABLE),
                ),
            ],
        )
        value = "Hello, world!"
        data = ObjectDefinitionTestObject(value)
        assert sut.dump(data) == {field_name: value}
