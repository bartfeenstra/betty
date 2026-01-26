from collections.abc import Sequence

from betty.collections import KeyedCollection
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.mapping import TypedMappingDefinition
from betty.data.indicator.selector import Key
from betty.data.str import StrDefinition
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
    _sut_unordered = KeyedCollectionDefinition[dict[str, str]](
        item=_item,
        key=Key("key"),
        ordered=False,
        label=DUMMY_LOCALIZABLE,
    )
    _sut_ordered = KeyedCollectionDefinition[dict[str, str]](
        item=_item,
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
                KeyedCollection(self._values, key=lambda value: value["key"])
            )
        ) == [(Key("my_first_key"), self._item)]

    def test_load__unordered(self) -> None:
        data = self._sut_unordered.porter.load(self._portable_unordered)
        assert isinstance(data, KeyedCollection)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_load__ordered(self) -> None:
        data = self._sut_ordered.porter.load(self._portable_ordered)
        assert isinstance(data, KeyedCollection)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_dump__unordered(self) -> None:
        data = KeyedCollection(self._values, key=lambda value: value["key"])
        assert self._sut_unordered.porter.dump(data) == self._portable_unordered

    def test_dump__ordered(self) -> None:
        data = KeyedCollection(self._values, key=lambda value: value["key"])
        assert self._sut_ordered.porter.dump(data) == self._portable_ordered
