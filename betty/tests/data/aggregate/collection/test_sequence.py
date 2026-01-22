import pytest

from betty.data import DataDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.str import StrDefinition
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestSequenceDefinition:
    def test_elements__should_contain_exactly_one_element(self) -> None:
        item = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=item,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.item is item

    def test_load__without_items(self) -> None:
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.load([]) == []

    def test_load__with_items(self) -> None:
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.load(["Hello, world!"]) == ["Hello, world!"]

    def test_load__with_factory(self) -> None:
        class FactoryList(list[str]):
            pass

        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
            factory=FactoryList,
        )
        assert isinstance(sut.load([]), FactoryList)

    def test_load__with_item_not_loadable(self) -> None:
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.load(["Hello, world!"])

    def test_dump__without_items(self) -> None:
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.dump([]) == []

    def test_dump__with_items(self) -> None:
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.dump(["Hello, world!"]) == ["Hello, world!"]

    def test_dump__with_item_not_dumpable(self) -> None:
        sut = SequenceDefinition[list[str]](
            cls=list[str],
            item=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.dump(["Hello, world!"])
