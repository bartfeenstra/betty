"""
Adapters between Betty and Python sequences.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from contextlib import suppress
from typing import TYPE_CHECKING, Any, overload, override

from betty.collection.sequence import MutableResolvedSequence

if TYPE_CHECKING:
    from betty.collections import ValueResolver


class ResolvedSequenceAdapter[ValueT, ResolvableValueT](Sequence[ValueT]):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    def __init__(
        self,
        values: Sequence[ValueT],
        /,
        *,
        value_resolver: ValueResolver[ValueT, ResolvableValueT],
    ):
        self._values = values
        self._value_resolver = value_resolver

    @overload
    def __getitem__(self, index: int) -> ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[ValueT]:
        pass

    def __getitem__(self, index):
        return self._values[index]

    def __len__(self):
        return len(self._values)

    def __contains__(self, value: Any) -> bool:
        with suppress(Exception):
            value = self._value_resolver(value)
        return value in self._values

    @override
    def index(self, value: Any, start: int = 0, stop: int | None = None) -> int:
        with suppress(Exception):
            value = self._value_resolver(value)
        args = (value, start)
        if stop is not None:
            args = (*args, stop)
        return self._values.index(*args)


class MutableResolvedSequenceAdapter[ValueT, ResolvableValueT](
    ResolvedSequenceAdapter[ValueT, ResolvableValueT],
    MutableResolvedSequence[ValueT, ResolvableValueT],
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    _values: MutableSequence[ValueT]

    def __init__(
        self,
        values: MutableSequence[ValueT],
        /,
        *,
        value_resolver: ValueResolver[ValueT, ResolvableValueT],
    ):
        super().__init__(values, value_resolver=value_resolver)

    @override
    def insert(self, index: int, value: ValueT | ResolvableValueT) -> None:
        self._values.insert(index, self._value_resolver(value))

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
            self._values[index] = self._value_resolver(value)
        else:
            self._values[index] = map(self._value_resolver, value)

    def __delitem__(self, index: int | slice) -> None:
        del self._values[index]

    @override
    def extend(self, values: Iterable[ValueT | ResolvableValueT]) -> None:
        self._values.extend(map(self._value_resolver, values))
