"""
Sequences.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, MutableSequence
from typing import overload, override

from betty.collection import ExtendableCollection, ResolvableValueCollection


class MutableBettySequence[ValueT, ResolvableValueT](
    ExtendableCollection[ValueT, ResolvableValueT],
    MutableSequence[ValueT],
    ResolvableValueCollection[ValueT, ResolvableValueT],
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
