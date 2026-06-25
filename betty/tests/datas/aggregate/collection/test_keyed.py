from collections.abc import Iterable, Sequence
from typing import ClassVar

import pytest

from betty.collection.keyed import MutableKeyedCollection
from betty.collections.keyed.adapter import MutableKeyedCollectionAdapter
from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.mapping import TypedMappingDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Key
from betty.portable import PortableData


class TestKeyedCollectionDefinition:
    _item = TypedMappingDefinition[dict[str, str]](
        cls=dict,
        label="-",
        fields={
            Key("key"): FieldDefinition(StrDefinition(label="-")),
            Key("other_element"): FieldDefinition(StrDefinition(label="-")),
        },
    )
    _sut_unordered = KeyedCollectionDefinition[
        MutableKeyedCollection[str, str, dict[str, str], dict[str, str]],
        dict[str, str],
        Key,
    ](
        value=_item,
        key=Key("key"),
        label="-",
        factory=lambda: MutableKeyedCollectionAdapter(key=lambda value: value["key"]),
    )
    _sut_ordered = KeyedCollectionDefinition[
        MutableKeyedCollection[str, str, dict[str, str], dict[str, str]],
        dict[str, str],
        Key,
    ](
        value=_item,
        key=Key("key"),
        order_dump=True,
        label="-",
        factory=lambda: MutableKeyedCollectionAdapter(key=lambda value: value["key"]),
    )
    _portable_unordered: ClassVar[PortableData] = {
        "my_first_key": {
            "other_element": "my_first_other_element",
        }
    }
    _portable_ordered: ClassVar[PortableData] = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]
    _values: ClassVar[Sequence[dict[str, str]]] = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]

    def test_load__unordered(self) -> None:
        data = self._sut_unordered.porter.load(self._portable_unordered)
        assert isinstance(data, MutableKeyedCollectionAdapter)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_load__ordered(self) -> None:
        data = self._sut_ordered.porter.load(self._portable_ordered)
        assert isinstance(data, MutableKeyedCollectionAdapter)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_dump__unordered(self) -> None:
        data = MutableKeyedCollectionAdapter(
            self._values, key=lambda value: value["key"]
        )
        assert self._sut_unordered.porter.dump(data) == self._portable_unordered

    def test_dump__ordered(self) -> None:
        data = MutableKeyedCollectionAdapter(
            self._values, key=lambda value: value["key"]
        )
        assert self._sut_ordered.porter.dump(data) == self._portable_ordered

    def test_clear(self) -> None:
        data = MutableKeyedCollectionAdapter(
            ({"key": "qux"},), key=lambda value: value["key"]
        )
        self._sut_unordered.clear(data)
        assert not data

    @pytest.mark.parametrize(
        ("expected", "data", "values"),
        [
            ([], MutableKeyedCollectionAdapter(key=lambda value: value["key"]), ()),
            (
                [{"key": "foo"}, {"key": "bar"}],
                MutableKeyedCollectionAdapter(
                    ({"key": "qux"},), key=lambda value: value["key"]
                ),
                ({"key": "foo"}, {"key": "bar"}),
            ),
            (
                [],
                MutableKeyedCollectionAdapter(
                    ({"key": "qux"},), key=lambda value: value["key"]
                ),
                (),
            ),
        ],
    )
    def test_replace(
        self,
        expected: list[str],
        data: MutableKeyedCollection[str, str, dict[str, str], dict[str, str]],
        values: Iterable[dict[str, str]],
    ) -> None:
        self._sut_unordered.replace(data, values)
        assert list(data) == expected
