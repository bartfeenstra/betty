from collections.abc import Iterable

import pytest

from betty.data import DataDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.str import StrDefinition
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestSequenceDefinition:
    def test_elements__should_contain_exactly_one_element(self) -> None:
        item = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=item,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.item is item

    def test_load__without_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.load([]) == []

    def test_load__with_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.load(["Hello, world!"]) == ["Hello, world!"]

    def test_load__with_factory(self) -> None:
        class FactoryList(list[str]):
            pass

        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
            factory=FactoryList,
        )
        assert isinstance(sut.porter.load([]), FactoryList)

    def test_load__with_item_not_loadable(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.porter.load(["Hello, world!"])

    def test_dump__without_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.dump([]) == []

    def test_dump__with_items(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.dump(["Hello, world!"]) == ["Hello, world!"]

    def test_dump__with_item_not_dumpable(self) -> None:
        sut = SequenceDefinition[list[str], str](
            cls=list,
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.porter.dump(["Hello, world!"])

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
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        ).replace(data, values)
        assert data == expected
