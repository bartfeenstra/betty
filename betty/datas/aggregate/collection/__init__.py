"""
Collection data types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Final, Self, final

from betty.data import (
    DataDefinition,
    PortableDataDefinition,
    PortableDataDefinitionBase,
    ResolvableDataDefinition,
    ResolvableDataPorter,
    resolve_data_definition,
)

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable

type CollectionManufacturer[DataT, NewT: Iterable] = Callable[[NewT | None], DataT]


class CollectionDefinition[CollectionT: Collection, ItemT, NewT: Iterable](
    PortableDataDefinitionBase[CollectionT], metaclass=ABCMeta
):
    """
    A homogenous collection data definition.
    """

    def __init__(
        self,
        *,
        item: ResolvableDataDefinition[PortableDataDefinition[ItemT]],
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        porter: ResolvableDataPorter[Self, CollectionT],
        manufacturer: CollectionManufacturer[CollectionT, NewT] | None = None,
    ):
        super().__init__(
            label=label,
            description=description,
            porter=porter,  # ty: ignore[invalid-argument-type]
        )
        self.item: Final[DataDefinition[ItemT]] = resolve_data_definition(item)
        """
        The definition of the items contained by this collection.
        """
        self.__manufacturer = manufacturer

    @final
    def new(self, values: NewT | None = None, /) -> CollectionT:
        """
        Create a new collection.
        """
        if not self.__manufacturer:
            raise TypeError(
                "This definition does not have a manufacturer. Either set a data class, or provide a manufacturer when initializing the definition."
            )
        return self.__manufacturer(values)


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
