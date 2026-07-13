"""
Keyed collection definitions.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, final, override

from betty.assertions.mapping import assert_mapping
from betty.assertions.sequence import assert_sequence
from betty.collection.keyed import MutableKeyedCollection
from betty.datas.aggregate.collection import CollectionDefinition
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.portable import (
        KeyedPorter,
        PortableData,
        PortableMapping,
        PortableSequence,
    )


class KeyedCollectionDefinition[
    MutableKeyedCollectionT: MutableKeyedCollection,
    ValueT,
](CollectionDefinition[MutableKeyedCollectionT, Iterable[ValueT]]):
    """
    A definition for :py:class:`betty.collection.keyed.MutableKeyedCollection`.
    """

    def __init__(
        self,
        *,
        cls: type[MutableKeyedCollection] | None = None,
        value: ResolvableDataDefinition[DataDefinition[ValueT, KeyedPorter[ValueT]]],
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
        self._order_dump = order_dump

    def _load(self, portable: PortableData, /) -> MutableKeyedCollectionT:
        if self._order_dump:
            values = assert_sequence(self.item.porter.load)(portable)
        else:
            values = [
                self._item.porter.load_keyed(*x)
                for x in assert_mapping()(portable).items()
            ]

        loaded = self.new()
        loaded.add(*values)
        return loaded

    def _dump(
        self, data: MutableKeyedCollectionT
    ) -> PortableMapping | PortableSequence:
        if self._order_dump:
            return [self.item.porter.dump(value) for value in data]
        return dict(self._item.porter.dump_keyed(item_data) for item_data in data)

    @final
    @override
    def clear(self, data: MutableKeyedCollectionT, /) -> None:
        data.clear()

    @final
    @override
    def replace(
        self, data: MutableKeyedCollectionT, values: Iterable[ValueT], /
    ) -> None:
        data.clear()
        data.add(*values)
