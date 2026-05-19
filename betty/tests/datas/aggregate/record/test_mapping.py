from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.mapping import TypedMappingDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Key


class TestTypedMappingDefinition:
    def test_load(self) -> None:
        field_name = "my_first_element"
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label="-",
            fields={
                Key(field_name): FieldDefinition(StrDefinition(label="-")),
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
            label="-",
            fields={
                Key(field_name): FieldDefinition(StrDefinition(label="-")),
            },
            factory=FactoryDict,
        )
        assert isinstance(sut.porter.load({field_name: "Hello, world!"}), FactoryDict)

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = TypedMappingDefinition[dict[str, str]](
            cls=dict,
            label="-",
            fields={
                Key(field_name): FieldDefinition(StrDefinition(label="-")),
            },
        )
        value = "Hello, world!"
        data = {field_name: value}
        assert sut.porter.dump(data) == {field_name: value}
