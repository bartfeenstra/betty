import pytest

from betty.data import DataDefinition
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.indicator.selector import Key
from betty.data.str import StrDefinition
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestMappingDefinition:
    def test_elements(self) -> None:
        item = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=item,
            label=DUMMY_LOCALIZABLE,
        )
        assert list(sut.elements({"key": "value"})) == [(Key("key"), item)]

    def test_item(self) -> None:
        item = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=item,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.item is item

    def test_load__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.load({}) == {}

    def test_load__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.load({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_load__with_factory(self) -> None:
        class FactoryDict(dict[str, str]):
            pass

        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
            factory=FactoryDict,
        )
        assert isinstance(sut.load({}), FactoryDict)

    def test_load__with_item_not_loadable(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.load({"hello": "Hello, world!"})

    def test_dump__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.dump({}) == {}

    def test_dump__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.dump({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_dump__with_item_not_dumpable(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict[str, str],
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            item=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.dump({"hello": "Hello, world!"})
