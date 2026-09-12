from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.str import StrDefinition
from betty.plugin import factory


class TestListDefinition:
    def test_factory__without_value(self) -> None:
        ListDefinition(label="-", value=StrDefinition(label="-"))
        assert factory.new() == []

    def test_factory__with_value(self) -> None:
        ListDefinition(label="-", value=StrDefinition(label="-"))
        assert factory.new(("Hello", "world!")) == ["Hello", "world!"]
