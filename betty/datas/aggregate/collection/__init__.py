"""
Collection data types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Any, Final, final

from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.portable import Porter


class CollectionDefinition[CollectionT: Collection, ValuesSetT: Iterable](
    DataDefinition[CollectionT], metaclass=ABCMeta
):
    """
    A homogenous collection data definition.
    """

    def __init__(
        self,
        *,
        cls: type[CollectionT] | None = None,
        item: ResolvableDataDefinition[DataDefinition[Any]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[CollectionT] | None = None,
        factory: Callable[[], CollectionT] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description, porter=porter)
        self.item: Final[DataDefinition[Any]] = resolve_data_definition(item)
        """
        The definition of the items contained by this collection.
        """
        self.__factory = factory

    @property
    def _factory(self) -> Callable[..., CollectionT]:
        if self.__factory:
            return self.__factory
        if self.cls:
            return self.cls
        raise ValueError(
            "This definition does not have a factory. Either set a data class, or provide a factory when initializing the definition."
        )

    @final
    def new(self, values: ValuesSetT | None = None) -> CollectionT:
        """
        Create a new collection.
        """
        new = self._factory()
        if values is not None:
            self.replace(new, values)
        return new

    @abstractmethod
    def clear(self, data: CollectionT, /) -> None:
        """
        Clear (remove) all values from the collection.
        """

    @abstractmethod
    def replace(self, data: CollectionT, values: ValuesSetT, /) -> None:
        """
        Replace all values in the collection with the given ones.
        """
