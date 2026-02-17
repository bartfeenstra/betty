"""
Keyed collection data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from betty.assertion import assert_mapping, assert_sequence
from betty.collections import MutableDictKeyedCollection, MutableKeyedCollection
from betty.data import Data
from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Element
from betty.portable import (
    CallbackPorter,
    PortableData,
    PortableMapping,
    PortableSequence,
)

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data
    from betty.data.aggregate.record import RecordDefinition
    from betty.locale.localizable import ResolvableLocalizable


@final
class KeyedCollectionDefinition[ValueT, ElementT: Element[str] = Element[str]](
    CollectionDefinition[MutableKeyedCollection[Any, Any, ValueT, Any], ElementT]
):
    """
    A definition for :py:class:`betty.collections.MutableKeyedCollection`.
    """

    _item: RecordDefinition[ValueT, ElementT]

    def __init__(
        self,
        *,
        value: RecordDefinition[ValueT, ElementT]
        | type[Intersection[ValueT, Data[RecordDefinition[Any, ElementT]]]],
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

    def _load(
        self, portable: PortableData, /
    ) -> MutableKeyedCollection[str, str, ValueT, Any]:
        if self._ordered:
            items = assert_sequence(self._item.porter.load)(portable)
        else:
            items = [
                self._item.porter.load_key(portable_item, self._key, portable_key)
                for portable_key, portable_item in assert_mapping()(portable).items()
            ]

        return MutableDictKeyedCollection(items, key=self._key.get)

    def _dump(
        self, data: MutableKeyedCollection[str, str, ValueT, Any]
    ) -> PortableMapping | PortableSequence:
        if self._ordered:
            return [self._item.porter.dump(value) for value in data]
        return dict(
            self._item.porter.dump_key(item_data, self._key) for item_data in data
        )
