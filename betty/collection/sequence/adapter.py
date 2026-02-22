"""
Adapters between Betty and Python sequences.
"""

from collections.abc import Callable, Iterable, MutableSequence, Sequence
from contextlib import suppress
from typing import Any, final, overload, override

from betty.collection.sequence import MutableResolvedSequence


class _ResolvedSequenceAdapter[ValueT, ResolvableValueT](Sequence[ValueT]):
    def __init__(
        self,
        upstream: Sequence[ValueT],
        *,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT],
    ):
        self._upstream = upstream
        self._value_resolver = value_resolver

    @overload
    def __getitem__(self, index: int) -> ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[ValueT]:
        pass

    @final
    def __getitem__(self, index):
        return self._upstream[index]

    @final
    def __len__(self):
        return len(self._upstream)

    @final
    def __contains__(self, value: Any) -> bool:
        with suppress(Exception):
            value = self._value_resolver(value)
        return value in self._upstream

    @final
    @override
    def index(self, value: Any, start: int = 0, stop: int = -1) -> int:
        with suppress(Exception):
            value = self._value_resolver(value)
        return self._upstream.index(value, start, stop)


@final
class ResolvedSequenceAdapter[ValueT, ResolvableValueT](
    _ResolvedSequenceAdapter[ValueT, ResolvableValueT]
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """


@final
class MutableResolvedSequenceAdapter[ValueT, ResolvableValueT](
    _ResolvedSequenceAdapter[ValueT, ResolvableValueT],
    MutableResolvedSequence[ValueT, ResolvableValueT],
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    _upstream: MutableSequence[ValueT]

    def __init__(
        self,
        upstream: MutableSequence[ValueT],
        *,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT],
    ):
        super().__init__(upstream, value_resolver=value_resolver)

    @override
    def insert(self, index: int, value: ValueT | ResolvableValueT) -> None:
        self._upstream.insert(index, self._value_resolver(value))

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
            self._upstream[index] = self._value_resolver(value)
        else:
            self._upstream[index] = map(self._value_resolver, value)

    def __delitem__(self, index: int | slice) -> None:
        del self._upstream[index]

    @override
    def extend(self, values: Iterable[ValueT | ResolvableValueT]) -> None:
        self._upstream.extend(map(self._value_resolver, values))
