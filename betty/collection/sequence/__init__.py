"""
Sequence types and implementations.
"""

from abc import abstractmethod
from collections.abc import Iterable, MutableSequence
from typing import overload, override

from betty.collection import MutableCollection


class MutableResolvedSequence[ValueT, ResolvableValueT](
    MutableSequence[ValueT], MutableCollection[ValueT]
):
    """
    A mutable sequence of resolved values.
    """

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

    @override
    @abstractmethod
    def extend(self, values: Iterable[ValueT | ResolvableValueT]) -> None:
        pass
