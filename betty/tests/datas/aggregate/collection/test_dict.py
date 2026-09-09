from betty.datas.aggregate.collection.dict import DictDefinition
from betty.datas.str import StrDefinition


class TestDictDefinition:
    def test_factory__without_value(self) -> None:
        sut = DictDefinition(
            label="-", key=StrDefinition(label="-"), value=StrDefinition(label="-")
        )
        assert sut.new() == {}

    def test_factory__with_value(self) -> None:
        sut = DictDefinition(
            label="-", key=StrDefinition(label="-"), value=StrDefinition(label="-")
        )
        assert sut.new([("Hello", "world!")]) == {"Hello": "world!"}
