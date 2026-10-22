"""
Collection data tpes.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection
from typing import override


class MutableCollection[T](Collection[T]):
    """
    A mutable collection of data.
    """

    __slots__ = ()

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """


class MutableValueCollection[T, ResolvableT](MutableCollection[T]):
    """
    A mutable collection of values.
    """

    __slots__ = ()

    @abstractmethod
    def add(self, *values: T | ResolvableT) -> None:
        """
        Add one or more values to the collection.
        """


class MutableOrderedValueCollection[T, ResolvableT](
    MutableValueCollection[T, ResolvableT]
):
    """
    A mutable, ordered collection of values.
    """

    __slots__ = ()

    @override
    def add(self, *values: T | ResolvableT) -> None:
        self.append(*values)

    @abstractmethod
    def append(self, *values: T | ResolvableT) -> None:
        """
        Append one or more values to the collection.
        """
