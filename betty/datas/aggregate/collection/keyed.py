"""
Keyed collection definitions.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, final, override

from betty.assertions.mapping import assert_mapping
from betty.assertions.sequence import assert_sequence
from betty.collection.keyed import KeyedCollection, MutableKeyedCollection
from betty.datas.aggregate.collection import (
    CollectionDefinition,
    DataFactory,
    MutableCollectionDefinition,
)
from betty.portable import (
    KeyedPorter,
)
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.portable import (
        PortableData,
        PortableMapping,
        PortableSequence,
    )


class KeyedCollectionDefinition[KeyedCollectionT: KeyedCollection, ValueT](
    CollectionDefinition[KeyedCollectionT, ValueT, Iterable[ValueT]]
):
    """
    A definition for :py:class:`betty.collection.keyed.KeyedCollection`.
    """

    def __init__(
        self,
        *,
        cls: type[MutableKeyedCollection] | None = None,
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        order_dump: bool = False,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: DataFactory[KeyedCollectionT, Iterable[ValueT]] | None = None,
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
        value_porter = self.item.porter
        assert isinstance(value_porter, KeyedPorter)
        self._value_porter: KeyedPorter[ValueT] = value_porter

    def _load(self, portable: PortableData, /) -> KeyedCollectionT:
        if self._order_dump:
            values = assert_sequence(self._value_porter.load)(portable)
            # @todo Riiiight, depending on mutability, the initial values have a different type.
            # @todo
            # @todo
            # @todo
        else:
            values = [
                self._value_porter.load_keyed(*x)
                for x in assert_mapping()(portable).items()
            ]
        return self.new(values)

    def _dump(self, data: KeyedCollectionT) -> PortableMapping | PortableSequence:
        if self._order_dump:
            return [self._value_porter.dump(value) for value in data]
        return dict(self._value_porter.dump_keyed(item_data) for item_data in data)


class MutableKeyedCollectionDefinition[
    KeyedCollectionT: MutableKeyedCollection,
    ValueT,
](
    KeyedCollectionDefinition[KeyedCollectionT, ValueT],
    MutableCollectionDefinition[KeyedCollectionT, ValueT, Iterable[ValueT]],
):
    """
    A definition for :py:class:`betty.collection.keyed.MutableKeyedCollection`.
    """

    @final
    @override
    def clear(self, data: KeyedCollectionT, /) -> None:
        data.clear()

    @final
    @override
    def replace(self, data: KeyedCollectionT, values: Iterable[ValueT], /) -> None:
        data.clear()
        data.add(*values)
