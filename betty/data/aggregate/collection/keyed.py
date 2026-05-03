"""
Keyed collection definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from betty.assertion import assert_mapping, assert_sequence
from betty.collection.keyed import KeyedCollection, MutableKeyedCollection
from betty.data.aggregate.collection import CollectionDefinition
from betty.indicator.selector import Element
from betty.portable import (
    CallbackPorter,
    PortableData,
    PortableMapping,
    PortableSequence,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data
    from betty.data.aggregate.record import RecordDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


@final
class KeyedCollectionDefinition[
    MutableKeyedCollectionT: MutableKeyedCollection = MutableKeyedCollection,
    ElementT: Element[str] = Element[str],
](CollectionDefinition[MutableKeyedCollectionT, ElementT]):
    """
    A definition for :py:class:`betty.collection.keyed.MutableKeyedCollection`.
    """

    _item: RecordDefinition[Any, ElementT]

    def __init__[KeyT, ValueT](
        self,
        /,
        cls: type[MutableKeyedCollection] | None = None,
        *,
        value: RecordDefinition[ValueT, ElementT]
        | type[Intersection[ValueT, Data[RecordDefinition[Any, ElementT]]]],
        key: ElementT,
        order_dump: bool = False,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[], MutableKeyedCollectionT] | None = None,
    ):
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
            item=value,
            factory=factory,
        )
        self._key = key
        self._order_dump = order_dump

    def _load(self, portable: PortableData, /) -> MutableKeyedCollection:
        if self._order_dump:
            values = assert_sequence(self._item.porter.load)(portable)
        else:
            values = [
                self._item.porter.load_key(portable_item, self._key, portable_key)
                for portable_key, portable_item in assert_mapping()(portable).items()
            ]

        loaded = self.new()
        loaded.add(*values)
        return loaded

    def _dump(self, data: KeyedCollection) -> PortableMapping | PortableSequence:
        if self._order_dump:
            return [self._item.porter.dump(value) for value in data]
        return dict(
            self._item.porter.dump_key(item_data, self._key) for item_data in data
        )
