"""
Catalog definitions.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, final, override

from betty.assertions.mapping import assert_mapping
from betty.assertions.sequence import assert_sequence
from betty.collection.catalog import Catalog, MutableCatalog
from betty.datas.aggregate.collection import (
    CollectionDefinition,
    CollectionManufacturer,
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


class CatalogDefinition[CatalogT: Catalog, ValueT](
    CollectionDefinition[CatalogT, ValueT, Iterable[ValueT]]
):
    """
    A definition for :py:class:`betty.collection.catalog.Catalog`.
    """

    def __init__(
        self,
        *,
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        order_dump: bool = False,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        manufacturer: CollectionManufacturer[CatalogT, Iterable[ValueT]] | None = None,
    ):
        super().__init__(
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
            item=value,
            manufacturer=manufacturer,
        )
        self._order_dump = order_dump
        value_porter = self.item.porter
        assert isinstance(value_porter, KeyedPorter)
        self._value_porter: KeyedPorter[ValueT] = value_porter

    def _load(self, portable: PortableData, /) -> CatalogT:
        if self._order_dump:
            values = assert_sequence(self._value_porter.load)(portable)
        else:
            values = [
                self._value_porter.load_keyed(*x)
                for x in assert_mapping()(portable).items()
            ]
        return self.new(values)

    def _dump(self, data: CatalogT) -> PortableMapping | PortableSequence:
        if self._order_dump:
            return [self._value_porter.dump(value) for value in data]
        return dict(self._value_porter.dump_keyed(item_data) for item_data in data)


class MutableCatalogDefinition[
    CatalogT: MutableCatalog,
    ValueT,
](
    CatalogDefinition[CatalogT, ValueT],
    MutableCollectionDefinition[CatalogT, ValueT, Iterable[ValueT]],
):
    """
    A definition for :py:class:`betty.collection.catalog.MutableCatalog`.
    """

    @final
    @override
    def clear(self, data: CatalogT, /) -> None:
        data.clear()

    @final
    @override
    def replace(self, data: CatalogT, values: Iterable[ValueT], /) -> None:
        data.clear()
        data.add(*values)
