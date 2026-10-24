"""
Collection data tpes.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable, Collection
from typing import Any

# @todo Can we constrain KeyT to a protocol that indicates a type is comparable?
# @todo
# @todo
type Keyer[ItemT, KeyT] = Callable[[ItemT], KeyT]


class MutableCollection[ItemT](Collection[ItemT]):
    """
    A mutable collection of data.
    """

    __slots__ = ()

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """


class AddableCollection[ItemT, ResolvableItemT](MutableCollection[ItemT]):
    """
    A mutable collection to which items can be added.
    """

    __slots__ = ()

    @abstractmethod
    def add(self, *items: ItemT | ResolvableItemT) -> None:
        """
        Add one or more items to the collection.

        If an item already exists in the collection, what happens is up to the implementation.
        """


class AppendableCollection[ItemT, ResolvableItemT](MutableCollection[ItemT]):
    """
    An ordered collection to which items can be appended.
    """

    __slots__ = ()

    @abstractmethod
    def append(self, *items: ItemT | ResolvableItemT) -> None:
        """
        Append one or more items to the collection.
        """


class ReversibleCollection[ItemT](MutableCollection[ItemT]):
    @abstractmethod
    def reverse(self) -> None:
        """
        Reverse the order of the items.
        """


class SortableCollection[ItemT](MutableCollection[ItemT]):
    @abstractmethod
    def sort(
        self, *, key: Keyer[ItemT, Any] | None = None, reverse: bool = False
    ) -> None:
        """
        Sort the items.

        If ``key`` is ``None``, sort the items themselves. Otherwise, sort the items using ``key``'s return value for
        each item.
        """
