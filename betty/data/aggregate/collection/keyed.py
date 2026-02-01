"""
Keyed collection data types.
"""

from collections.abc import Sequence
from typing import Any, TypeVar, final

from typing_extensions import override

from betty.assertion import assert_mapping, assert_sequence
from betty.collections import MutableDictKeyedCollection, MutableKeyedCollection
from betty.data import Data, DataDefinition
from betty.data.aggregate.collection import CollectionDefinition
from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Element, Key
from betty.locale.localizable import ResolvableLocalizable
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
    CollectionDefinition[MutableKeyedCollection[Any, Any, _ValueT, Any], Key]
):
    """
    A definition for :py:class:`betty.collections.MutableKeyedCollection`.
    """

    _item: RecordDefinition[_ValueT, Key]

    def __init__(
        self,
        *,
        value: RecordDefinition[_ValueT] | type[Data[RecordDefinition]],
        key: Element[str],
        ordered: bool,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=MutableKeyedCollection,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
            item=value,
        )
        self._key = key
        self._ordered = ordered

    @override
    def elements(
        self, data: MutableKeyedCollection[Any, Any, _ValueT, Any]
    ) -> Sequence[tuple[Key, DataDefinition]]:
        return [(Key(self._key.get(item_data)), self.item) for item_data in data]

    def _load(
        self, portable: PortableData, /
    ) -> MutableKeyedCollection[str, str, _ValueT, Any]:
        if self._ordered:
            items = assert_sequence(self._item.porter.load)(portable)
        else:
            items = [
                self._item.porter.load_key(portable_item, self._key, portable_key)
                for portable_key, portable_item in assert_mapping()(portable).items()
            ]

        return MutableDictKeyedCollection(items, key=self._key.get)

    def _dump(
        self, data: MutableKeyedCollection[str, str, _ValueT, Any]
    ) -> PortableMapping | PortableSequence:
        if self._ordered:
            return [self._item.porter.dump(value) for value in data]
        return dict(
            self._item.porter.dump_key(item_data, self._key) for item_data in data
        )
