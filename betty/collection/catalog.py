"""
Catalogs.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Iterable

from betty.collection import MutableCollection


class Catalog[KeyT, ResolvableKeyT, ValueT](Collection[ValueT]):
    """
    A catalog.

    This is different from a mapping in that iteration takes place over values, not keys, and that callers cannot
    necessarily associate keys with values themselves (this may be done automatically by implementations).
    """

    @abstractmethod
    def keys(self) -> Iterable[KeyT]:
        """
        Get an iterable over the collection's keys.
        """

    @abstractmethod
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        pass


class MutableCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    Catalog[KeyT, ResolvableKeyT, ValueT], MutableCollection[ValueT]
):
    """
    A mutable catalog.
    """

    # @todo add/append/prepend/insert and similar methods that change the collection's items, all depend on the type
    # @todo of collection (sorted, not sorted....). We should probably not have add() here...
    # @todo
    @abstractmethod
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        """
        Add one or more values to the collection.
        """

    @abstractmethod
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        """
        Remove one or more keys from the collection.
        """

    @abstractmethod
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        pass
