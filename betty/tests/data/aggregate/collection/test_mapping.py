from collections.abc import Sequence

import pytest

from betty.collections import PrimaryKeyCollection
from betty.data import DataDefinition
from betty.data.aggregate.collection.mapping import (
    KeyedCollectionDefinition,
    MappingDefinition,
)
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.mapping import TypedMappingDefinition
from betty.data.indicator.selector import Key
from betty.data.str import StrDefinition
from betty.portable import PortableData
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestMappingDefinition:
    def test_elements(self) -> None:
        item = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=item,
            label=DUMMY_LOCALIZABLE,
        )
        assert list(sut.elements({"key": "value"})) == [(Key("key"), item)]

    def test_item(self) -> None:
        item = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=item,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.item is item

    def test_load__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.load({}) == {}

    def test_load__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.load({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_load__with_factory(self) -> None:
        class FactoryDict(dict[str, str]):
            pass

        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
            factory=FactoryDict,
        )
        assert isinstance(sut.porter.load({}), FactoryDict)

    def test_load__with_item_not_loadable(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.porter.load({"hello": "Hello, world!"})

    def test_dump__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.dump({}) == {}

    def test_dump__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.dump({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_dump__with_item_not_dumpable(self) -> None:
        sut = MappingDefinition[dict[str, str]](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.porter.dump({"hello": "Hello, world!"})


class TestKeyedCollectionDefinition:
    _item = TypedMappingDefinition[dict[str, str]](
        cls=dict,
        label=DUMMY_LOCALIZABLE,
        fields=[
            FieldDefinition(Key("key"), StrDefinition(label=DUMMY_LOCALIZABLE)),
            FieldDefinition(
                Key("other_element"), StrDefinition(label=DUMMY_LOCALIZABLE)
            ),
        ],
    )
    _sut_unordered = KeyedCollectionDefinition[dict[str, str]](
        value=_item,
        key=Key("key"),
        ordered=False,
        label=DUMMY_LOCALIZABLE,
    )
    _sut_ordered = KeyedCollectionDefinition[dict[str, str]](
        value=_item,
        key=Key("key"),
        ordered=True,
        label=DUMMY_LOCALIZABLE,
    )
    _portable_unordered: PortableData = {
        "my_first_key": {
            "other_element": "my_first_other_element",
        }
    }
    _portable_ordered: PortableData = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]
    _values: Sequence[dict[str, str]] = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]

    def test_elements(self) -> None:
        assert list(
            self._sut_ordered.elements(
                PrimaryKeyCollection(self._values, key=lambda value: value["key"])
            )
        ) == [(Key("my_first_key"), self._item)]

    def test_load__unordered(self) -> None:
        data = self._sut_unordered.porter.load(self._portable_unordered)
        assert isinstance(data, PrimaryKeyCollection)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_load__ordered(self) -> None:
        data = self._sut_ordered.porter.load(self._portable_ordered)
        assert isinstance(data, PrimaryKeyCollection)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_dump__unordered(self) -> None:
        data = PrimaryKeyCollection(self._values, key=lambda value: value["key"])
        assert self._sut_unordered.porter.dump(data) == self._portable_unordered

    def test_dump__ordered(self) -> None:
        data = PrimaryKeyCollection(self._values, key=lambda value: value["key"])
        assert self._sut_ordered.porter.dump(data) == self._portable_ordered
