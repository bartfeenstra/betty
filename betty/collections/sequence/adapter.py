"""
Adapters between Betty and Python sequences.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence, Sequence
from contextlib import suppress
from typing import Any, overload, override

from betty.collection.sequence import MutableResolvedSequence


class ResolvedSequenceAdapter[ValueT, ResolvableValueT](Sequence[ValueT]):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    def __init__(
        self,
        proxied: Sequence[ValueT],
        *,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT],
    ):
        self._proxied = proxied
        self._value_resolver = value_resolver

    @overload
    def __getitem__(self, index: int) -> ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[ValueT]:
        pass

    def __getitem__(self, index):
        return self._proxied[index]

    def __len__(self):
        return len(self._proxied)

    def __contains__(self, value: Any) -> bool:
        with suppress(Exception):
            value = self._value_resolver(value)
        return value in self._proxied

    @override
    def index(self, value: Any, start: int = 0, stop: int | None = None) -> int:
        with suppress(Exception):
            value = self._value_resolver(value)
        args = (value, start)
        if stop is not None:
            args = (*args, stop)
        return self._proxied.index(*args)


class MutableResolvedSequenceAdapter[ValueT, ResolvableValueT](
    ResolvedSequenceAdapter[ValueT, ResolvableValueT],
    MutableResolvedSequence[ValueT, ResolvableValueT],
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    _proxied: MutableSequence[ValueT]

    def __init__(
        self,
        proxied: MutableSequence[ValueT],
        *,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT],
    ):
        super().__init__(proxied, value_resolver=value_resolver)

    @override
    def insert(self, index: int, value: ValueT | ResolvableValueT) -> None:
        self._proxied.insert(index, self._value_resolver(value))

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
            self._proxied[index] = self._value_resolver(value)
        else:
            self._proxied[index] = map(self._value_resolver, value)

    def __delitem__(self, index: int | slice) -> None:
        del self._proxied[index]

    @override
    def extend(self, values: Iterable[ValueT | ResolvableValueT]) -> None:
        self._proxied.extend(map(self._value_resolver, values))
