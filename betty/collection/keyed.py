"""
Keyed collection types and implementations.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Iterable

from betty.collection import MutableCollection


class KeyedCollection[KeyT, ResolvableKeyT, ValueT](Collection[ValueT]):
    """
    A collection of values that are accessible by their keys.

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


class MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    KeyedCollection[KeyT, ResolvableKeyT, ValueT],
    MutableCollection[ValueT],
):
    """
    A mutable ordered collection of values that are accessible by their keys.
    """

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
