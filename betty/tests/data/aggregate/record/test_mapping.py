from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.mapping import TypedMappingDefinition
from betty.data.indicator.selector import Key
from betty.data.str import StrDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestTypedMappingDefinition:
    def test_elements(self) -> None:
        element = FieldDefinition(
            Key("my_first_element"), StrDefinition(label=DUMMY_LOCALIZABLE)
        )
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields=[element],
        )
        assert list(sut.fields) == [element]

    def test_load(self) -> None:
        field_name = "my_first_element"
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Key(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            ],
        )
        value = "Hello, world!"
        data = sut.porter.load({field_name: value})
        assert data["my_first_element"] == value

    def test_load__with_factory(self) -> None:
        class FactoryDict(dict[str, str]):
            pass

        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Key("my_first_element"), StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            ],
            factory=FactoryDict,
        )
        assert isinstance(
            sut.porter.load({"my_first_element": "Hello, world!"}), FactoryDict
        )

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Key(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            ],
        )
        value = "Hello, world!"
        data = {field_name: value}
        assert sut.porter.dump(data) == {field_name: value}
