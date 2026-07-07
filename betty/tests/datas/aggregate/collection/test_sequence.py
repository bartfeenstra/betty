from collections.abc import Iterable

import pytest

from betty.data import DataDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.str import StrDefinition
from betty.portable.error import NotPortable


class TestSequenceDefinition:
    def test_elements__should_contain_exactly_one_element(self) -> None:
        item = StrDefinition(label="-")
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=item,
            label="-",
        )
        assert sut.item is item

    def test_porter__load__without_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.load([]) == []

    def test_porter__load__with_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.load(["Hello, world!"]) == ["Hello, world!"]

    def test_porter__load__with_factory(self) -> None:
        class FactoryList(list[str]):
            pass

        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label="-"),
            label="-",
            factory=FactoryList,
        )
        assert isinstance(sut.porter.load([]), FactoryList)

    def test_porter__load__with_item_not_loadable(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=DataDefinition(cls=str, label="-"),
            label="-",
        )
        with pytest.raises(NotPortable):
            sut.porter.load(["Hello, world!"])

    def test_porter__dump__without_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.dump([]) == []

    def test_porter__dump__with_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.dump(["Hello, world!"]) == ["Hello, world!"]

    def test_porter__dump__with_item_not_dumpable(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=DataDefinition(cls=str, label="-"),
            label="-",
        )
        with pytest.raises(NotPortable):
            sut.porter.dump(["Hello, world!"])

    def test_clear(self) -> None:
        data = ["foo", "bar"]
        SequenceDefinition[list[str], str](
            cls=list,
            value=DataDefinition(cls=str, label="-"),
            label="-",
        ).clear(data)
        assert not data

    @pytest.mark.parametrize(
        ("expected", "data", "values"),
        [
            ([], [], ()),
            (["foo", "bar"], ["qux"], ("foo", "bar")),
            ([], ["qux"], ()),
        ],
    )
    def test_replace(
        self, expected: list[str], data: list[str], values: Iterable[str]
    ) -> None:
        SequenceDefinition[list[str], str](
            cls=list,
            value=DataDefinition(cls=str, label="-"),
            label="-",
        ).replace(data, values)
        assert data == expected
