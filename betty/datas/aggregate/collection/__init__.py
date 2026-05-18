"""
Collection data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Any, final

from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate import AggregateDefinition
from betty.indicator.selector import Element

if TYPE_CHECKING:
    from betty.data import Data as Data
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableData, Porter


class CollectionDefinition[
    CollectionT: Collection,
    ValuesSetT: Iterable,
    ElementT: Element[Any],
](AggregateDefinition[CollectionT, ElementT], ABC):
    """
    A homogenous collection data definition.
    """

    def __init__(
        self,
        /,
        cls: type[CollectionT] | None = None,
        *,
        item: ResolvableDataDefinition[DataDefinition[Any, PortableData]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[CollectionT] | None = None,
        factory: Callable[[], CollectionT] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description, porter=porter)
        self._item = resolve_data_definition(item)
        self._factory = factory

    @final
    @property
    def item(self) -> DataDefinition[Any, PortableData]:
        """
        The definition of the items contained by this collection.
        """
        return self._item

    @final
    def new(self, values: ValuesSetT | None = None) -> CollectionT:
        """
        Create a new collection.
        """
        new = (self.cls if not self._factory else self._factory)()
        if values is not None:
            self.replace(new, values)
        return new

    @abstractmethod
    def replace(self, data: CollectionT, values: ValuesSetT, /) -> None:
        """
        Replace all values in the collection with the given ones.
        """
