"""
Collection data tpes.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Collection
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from ty_extensions import Intersection


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


class ResolvableKeyCollection[KeyT, ResolvableKeyT](metaclass=ABCMeta):
    """
    A collection that can resolve a wide range of data to its internal key type.
    """

    __slots__ = ()

    @abstractmethod
    def resolve_key(self, key: KeyT | ResolvableKeyT, /) -> KeyT:
        """
        Resolve a key.
        """


class ResolvableValueCollection[ValueT, ResolvableValueT](metaclass=ABCMeta):
    """
    A collection that can resolve a wide range of data to its internal value type.
    """

    __slots__ = ()

    @abstractmethod
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        """
        Resolve a value.
        """


class _OtherCollection[OtherT]:
    """
    A mixin class to ensure other classes all operate on the same type of 'other' collection.
    """


class AddableCollection[ValueT, ResolvableValueT](
    ResolvableValueCollection[ValueT, ResolvableValueT], MutableCollection[ValueT]
):
    """
    A mutable collection to which values can be added.
    """

    __slots__ = ()

    @abstractmethod
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        """
        Add one or more values to the collection, overwriting existing duplicates.
        """


class UpdatableCollection[ValueT, ResolvableValueT, OtherT](
    _OtherCollection[OtherT],
    ResolvableValueCollection[ValueT, ResolvableValueT],
    MutableCollection[ValueT],
):
    """
    A mutable collection that can be updated with new values.
    """

    __slots__ = ()

    @abstractmethod
    def update(self, *others: OtherT) -> None:
        """
        Update the collection with the values of all the others, overwriting existing duplicates.
        """


class AppendableCollection[ValueT, ResolvableValueT](
    ResolvableValueCollection[ValueT, ResolvableValueT], MutableCollection[ValueT]
):
    """
    An ordered collection to which values can be appended.
    """

    __slots__ = ()

    @abstractmethod
    def append(self, *values: ValueT | ResolvableValueT) -> None:
        """
        Append one or more values to the collection.
        """


class ExtendableCollection[ValueT, ResolvableValueT, OtherT](
    _OtherCollection[OtherT],
    ResolvableValueCollection[ValueT, ResolvableValueT],
    MutableCollection[ValueT],
):
    """
    An ordered collection that can be extended with new values.
    """

    __slots__ = ()

    @abstractmethod
    def extend(self, *others: OtherT) -> None:
        """
        Extend the collection with the values of all the others.
        """


class ReversibleCollection[ItemT](MutableCollection[ItemT]):
    """
    A collection that can reverse the order of its items.
    """

    __slots__ = ()

    @abstractmethod
    def reverse(self) -> None:
        """
        Reverse the order of the items.
        """


type SortKey[ItemT] = Callable[[ItemT], SupportsRichComparison]


class SortableCollection[ItemT](MutableCollection[ItemT]):
    """
    A collection whose items can be sorted in-place.
    """

    __slots__ = ()

    @overload
    def sort(
        self: Collection[Intersection[ItemT, SupportsRichComparison]],
        *,
        key: None = None,
        reverse: bool = False,
    ) -> None:
        pass

    @overload
    def sort(self, *, key: SortKey[ItemT] | None = None, reverse: bool = False) -> None:
        pass

    @abstractmethod
    def sort(self, *, key=None, reverse=False) -> None:
        """
        Sort the items.

        If ``key`` is ``None``, sort the items themselves. Otherwise, sort the items using ``key``'s return value for
        each item.
        """
