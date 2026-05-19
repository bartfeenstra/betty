from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.mapping import TypedMappingDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Key
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestTypedMappingDefinition:
    def test_load(self) -> None:
        field_name = "my_first_element"
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields={
                Key(field_name): FieldDefinition(
                    StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            },
        )
        value = "Hello, world!"
        data = sut.porter.load({field_name: value})
        assert data["my_first_element"] == value

    def test_load__with_factory(self) -> None:
        field_name = "my_first_element"

        class FactoryDict(dict[str, str]):
            pass

        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields={
                Key(field_name): FieldDefinition(
                    StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            },
            factory=FactoryDict,
        )
        assert isinstance(sut.porter.load({field_name: "Hello, world!"}), FactoryDict)

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label=DUMMY_LOCALIZABLE,
            fields={
                Key(field_name): FieldDefinition(
                    StrDefinition(label=DUMMY_LOCALIZABLE)
                ),
            },
        )
        value = "Hello, world!"
        data = {field_name: value}
        assert sut.porter.dump(data) == {field_name: value}
