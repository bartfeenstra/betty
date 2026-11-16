from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.str import StrDefinition


class TestListDefinition:
    def test_factory__without_value(self) -> None:
        sut = ListDefinition(label="-", value=StrDefinition(label="-"))
        assert list(sut.new()) == []

    def test_factory__with_value(self) -> None:
        sut = ListDefinition(label="-", value=StrDefinition(label="-"))
        assert list(sut.new(("Hello", "world!"))) == ["Hello", "world!"]
