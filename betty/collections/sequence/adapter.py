"""
Adapters between Betty and Python sequences.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from contextlib import suppress
from itertools import chain
from typing import TYPE_CHECKING, Any, overload, override

from betty.collection.sequence import MutableResolvableSequence
from betty.collections import ValueResolvable

if TYPE_CHECKING:
    from ty_extensions import Intersection


# This is a mixin to work around MRO issues with Generic and Sequence.
class _SequenceAdapter[ValueT, ResolvableValueT, WrappedT: Sequence](
    ValueResolvable[ValueT, ResolvableValueT]
):
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

    def index(self, value: Any, start: int = 0, stop: int | None = None) -> int:
        with suppress(Exception):
            value = self.resolve_value(value)
        args = (value, start)
        if stop is not None:
            args = (*args, stop)
        return self.__wrapped__.index(*args)


class SequenceAdapter[ValueT, ResolvableValueT, WrappedT: Sequence](
    _SequenceAdapter[ValueT, ResolvableValueT, WrappedT], Sequence[ValueT]
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    __slots__ = ()


class MutableSequenceAdapter[ValueT, ResolvableValueT, WrappedT: MutableSequence](
    _SequenceAdapter[ValueT, ResolvableValueT, WrappedT],
    MutableResolvableSequence[ValueT, ResolvableValueT],
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
    def append(self, *values: ValueT | ResolvableValueT) -> None:
        self.extend(values)

    @override
    def extend(self, *others: Any) -> None:
        self.__wrapped__.extend(map(self.resolve_value, chain(*others)))
