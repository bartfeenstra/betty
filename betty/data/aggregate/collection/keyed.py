"""
Keyed collection data types.
"""

from collections.abc import Sequence
from typing import Any, TypeVar, final

from typing_extensions import override

from betty.assertion import assert_mapping, assert_sequence
from betty.collections import KeyedCollection
from betty.data import DataDefinition
from betty.data.aggregate.collection import CollectionDefinition
from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Element, Key
from betty.locale.localizable import LocalizableLike
from betty.portable import (
    CallbackPorter,
    PortableData,
    PortableMapping,
    PortableSequence,
)

_ValueT = TypeVar("_ValueT")
_ElementT = TypeVar("_ElementT")


@final
class KeyedCollectionDefinition(
    CollectionDefinition[KeyedCollection[Any, _ValueT, Any, Any], Key]
):
    """
    A definition for :py:class:`betty.collections.KeyedCollection`.
    """

    _item: RecordDefinition[_ValueT, Key]

    def __init__(
        self,
        *,
        value: RecordDefinition[_ValueT],
        key: Element[str],
        ordered: bool,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            cls=KeyedCollection,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
            item=value,
        )
        self._key = key
        self._ordered = ordered

    @override
    def elements(
        self, data: KeyedCollection[Any, _ValueT, Any, Any]
    ) -> Sequence[tuple[Key, DataDefinition]]:
        return [(Key(self._key.get(item_data)), self.item) for item_data in data]

    def _load(
        self, portable: PortableData, /
    ) -> KeyedCollection[str, _ValueT, str, _ValueT]:
        if self._ordered:
            items = assert_sequence(self._item.porter.load)(portable)
        else:
            items = [
                self._item.porter.load_key(portable_item, self._key, portable_key)
                for portable_key, portable_item in assert_mapping()(portable).items()
            ]

        return KeyedCollection(items, key=self._key.get)

    def _dump(
        self, data: KeyedCollection[str, _ValueT, str, _ValueT]
    ) -> PortableMapping | PortableSequence:
        if self._ordered:
            return [self._item.porter.dump(value) for value in data]
        return dict(
            self._item.porter.dump_key(item_data, self._key) for item_data in data
        )
