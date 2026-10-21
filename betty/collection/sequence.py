"""
Sequences.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, MutableSequence
from typing import overload, override

from betty.collection import Appendable, Extendable


class MutableResolvableSequence[ValueT, ResolvableValueT](
    Appendable[ValueT, ResolvableValueT],
    Extendable[Iterable[ValueT | ResolvableValueT]],
    MutableSequence[ValueT],
):
    """
    A mutable sequence of resolved values.
    """

    __slots__ = ()

    @override
    @abstractmethod
    def insert(self, index: int, value: ValueT | ResolvableValueT) -> None:
        pass

    @overload
    def __setitem__(self, index: int, value: ValueT | ResolvableValueT) -> None:
        pass

    @overload
    def __setitem__(
        self, index: slice, value: Iterable[ValueT | ResolvableValueT]
    ) -> None:
        pass

    @abstractmethod
    def __setitem__(self, index, value):
        pass
