"""
Adapters between Betty and Python sequences.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from contextlib import suppress
from typing import Any, overload, override

from ty_extensions import Intersection

from betty.collection import ResolvedValueCollection
from betty.collection.sequence import MutableBettySequence


class SequenceAdapter[ValueT, ResolvableValueT, WrappedT: Sequence](
    Sequence[ValueT], ResolvedValueCollection[ValueT, ResolvableValueT]
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    __slots__ = ("__wrapped__",)

    def __init__(self, wrapped: Intersection[WrappedT, Sequence[ValueT]], /):
        self.__wrapped__ = wrapped

    @overload
    def __getitem__(self, index: int) -> ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[ValueT]:
        pass

    def __getitem__(self, index):
        return self.__wrapped__[index]

    def __len__(self):
        return len(self.__wrapped__)

    def __contains__(self, value: Any) -> bool:
        with suppress(Exception):
            value = self.resolve_value(value)
        return value in self.__wrapped__

    @override
    def index(self, value: Any, start: int = 0, stop: int | None = None) -> int:
        with suppress(Exception):
            value = self.resolve_value(value)
        args = (value, start)
        if stop is not None:
            args = (*args, stop)
        return self.__wrapped__.index(*args)


class MutableSequenceAdapter[ValueT, ResolvableValueT, WrappedT: MutableSequence](
    SequenceAdapter[
        ValueT, ResolvableValueT, Intersection[WrappedT, MutableSequence[ValueT]]
    ],
    MutableBettySequence[ValueT, ResolvableValueT],
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    __slots__ = ()

    @override
    def insert(self, index: int, value: ValueT | ResolvableValueT) -> None:
        self.__wrapped__.insert(index, self.resolve_value(value))

    @overload
    def __setitem__(self, index: int, value: ValueT | ResolvableValueT) -> None:
        pass

    @overload
    def __setitem__(
        self, index: slice, value: Iterable[ValueT | ResolvableValueT]
    ) -> None:
        pass

    def __setitem__(self, index, value):
        if isinstance(index, int):
            self.__wrapped__[index] = self.resolve_value(value)
        else:
            self.__wrapped__[index] = map(self.resolve_value, value)

    def __delitem__(self, index: int | slice) -> None:
        del self.__wrapped__[index]

    @override
    def extend(self, values: Iterable[ValueT | ResolvableValueT]) -> None:
        self.__wrapped__.extend(map(self.resolve_value, values))
