"""
Collection data tpes.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod


class Clearable(metaclass=ABCMeta):
    """
    A mutable collection of data.
    """

    __slots__ = ()

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """


class Otherable[OtherT]:
    """
    A mixin class to ensure other classes all operate on the same type of 'other' collection.
    """

    __slots__ = ()


class Addable[ValueT, ResolvableValueT](metaclass=ABCMeta):
    """
    A mutable collection to which values can be added.
    """

    __slots__ = ()

    @abstractmethod
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        """
        Add one or more values to the collection, overwriting existing duplicates.
        """


class Updatable[OtherT](Otherable[OtherT], metaclass=ABCMeta):
    """
    A mutable collection that can be updated with new values.
    """

    __slots__ = ()

    @abstractmethod
    def update(self, *others: OtherT) -> None:
        """
        Update the collection with the values of all the others, overwriting existing duplicates.
        """


class Appendable[ValueT, ResolvableValueT](metaclass=ABCMeta):
    """
    An ordered collection to which values can be appended.
    """

    __slots__ = ()

    @abstractmethod
    def append(self, *values: ValueT | ResolvableValueT) -> None:
        """
        Append one or more values to the collection.
        """


class Extendable[OtherT](Otherable[OtherT], metaclass=ABCMeta):
    """
    An ordered collection that can be extended with new values.
    """

    __slots__ = ()

    @abstractmethod
    def extend(self, *others: OtherT) -> None:
        """
        Extend the collection with the values of all the others.
        """
