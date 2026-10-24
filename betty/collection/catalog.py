"""
Catalogs.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Iterable

from betty.collection import AddableCollection


class Catalog[KeyT, ResolvableKeyT, ValueT](Collection[ValueT]):
    """
    A catalog.

    This is different from a mapping in that iteration takes place over values, not keys, and that callers cannot
    necessarily associate keys with values themselves (this may be done automatically by implementations).
    """

    __slots__ = ()

    @abstractmethod
    def keys(self) -> Iterable[KeyT]:
        """
        Get an iterable over the collection's keys.
        """

    @abstractmethod
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        pass


# @todo Do we want to add .pop()?
class MutableCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    Catalog[KeyT, ResolvableKeyT, ValueT], AddableCollection[ValueT, ResolvableValueT]
):
    """
    A mutable catalog.
    """

    __slots__ = ()

    @abstractmethod
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        """
        Remove one or more keys from the collection.
        """

    @abstractmethod
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        pass
