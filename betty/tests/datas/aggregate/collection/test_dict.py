from betty.datas.aggregate.collection.dict import DictDefinition
from betty.datas.str import StrDefinition
from betty.plugin import factory


class TestDictDefinition:
    def test_factory__without_value(self) -> None:
        DictDefinition(
            label="-", key=StrDefinition(label="-"), value=StrDefinition(label="-")
        )
        assert factory.new() == {}

    def test_factory__with_value(self) -> None:
        DictDefinition(
            label="-", key=StrDefinition(label="-"), value=StrDefinition(label="-")
        )
        assert factory.new([("Hello", "world!")]) == {"Hello": "world!"}
