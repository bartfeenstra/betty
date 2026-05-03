from collections.abc import Sequence
from typing import ClassVar

from betty.collection.keyed.adapter import MutableKeyedCollectionAdapter
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.mapping import TypedMappingDefinition
from betty.data.str import StrDefinition
from betty.indicator.selector import Key
from betty.portable import PortableData
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


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
    _sut_unordered = KeyedCollectionDefinition(
        value=_item,
        key=Key("key"),
        label=DUMMY_LOCALIZABLE,
        factory=lambda: MutableKeyedCollectionAdapter(key=lambda value: value["key"]),
    )
    _sut_ordered = KeyedCollectionDefinition(
        value=_item,
        key=Key("key"),
        order_dump=True,
        label=DUMMY_LOCALIZABLE,
        factory=lambda: MutableKeyedCollectionAdapter(key=lambda value: value["key"]),
    )
    _portable_unordered: ClassVar[PortableData] = {
        "my_first_key": {
            "other_element": "my_first_other_element",
        }
    }  # ty:ignore[invalid-assignment]
    _portable_ordered: ClassVar[PortableData] = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]  # ty:ignore[invalid-assignment]
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
