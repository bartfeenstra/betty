"""
Collection data types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Final, final

from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.portable import Porter


type DataFactory[DataT, NewT] = Callable[[NewT | None], DataT]


class CollectionDefinition[CollectionT: Collection, ItemT, NewT: Iterable](
    DataDefinition[CollectionT], metaclass=ABCMeta
):
    """
    A homogenous collection data definition.
    """

    def __init__(
        self,
        *,
        cls: type[CollectionT] | None = None,
        item: ResolvableDataDefinition[DataDefinition[ItemT]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[CollectionT] | None = None,
        factory: DataFactory[CollectionT, NewT] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description, porter=porter)
        self.item: Final[DataDefinition[ItemT]] = resolve_data_definition(item)
        """
        The definition of the items contained by this collection.
        """
        self.__factory = factory

    @final
    def new(self, values: NewT | None = None, /) -> CollectionT:
        """
        Create a new collection.
        """
        if not self.__factory:
            raise ValueError(
                "This definition does not have a factory. Either set a data class, or provide a factory when initializing the definition."
            )
        return self.__factory(values)


class MutableCollectionDefinition[CollectionT: Collection, ItemT, NewT: Iterable](
    CollectionDefinition[CollectionT, ItemT, NewT]
):
    """
    A mutable homogenous collection data definition.
    """

    @abstractmethod
    def clear(self, data: CollectionT, /) -> None:
        """
        Clear (remove) all values from the collection.
        """

    @abstractmethod
    def replace(self, data: CollectionT, values: NewT, /) -> None:
        """
        Replace all values in the collection with the given ones.
        """
