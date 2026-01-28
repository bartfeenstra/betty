"""
Collection data tpes.
"""

from collections.abc import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    MutableSequence,
    Sequence,
)
from typing import Generic, TypeVar, final, overload

from typing_extensions import override

from betty.functools import passthrough

_KeyT = TypeVar("_KeyT")
_ValueT = TypeVar("_ValueT")
_ResolvableKeyT = TypeVar("_ResolvableKeyT")
_ResolvableValueT = TypeVar("_ResolvableValueT")


@final
class KeyedCollection(
    Collection[_ValueT], Generic[_KeyT, _ValueT, _ResolvableKeyT, _ResolvableValueT]
):
    """
    A collection of values, automatically keyed.
    """

    def __init__(
        self,
        values: Iterable[_ResolvableValueT] | None = None,
        *,
        key: Callable[[_ValueT], _KeyT],
        key_resolver: Callable[[_ResolvableKeyT | _KeyT], _KeyT] = passthrough,
        value_resolver: Callable[[_ResolvableValueT | _KeyT], _ValueT] = passthrough,
        resolver: Callable[
            [Sequence[_ValueT]], Sequence[_ResolvableValueT | _ValueT]
        ] = passthrough,
    ):
        self._values = {}
        self._key = key
        self._key_resolver = key_resolver
        self._value_resolver = value_resolver
        self._resolver = resolver
        if values is not None:
            self.add(*values)

    @override
    def __len__(self) -> int:
        return self._values.__len__()

    @override
    def __iter__(self) -> Iterator[_ValueT]:
        yield from self._values.values()

    @override
    def __contains__(self, key: object) -> bool:
        try:
            return (
                self._key_resolver(
                    key,  # ty:ignore[invalid-argument-type]
                )
                in self._values
            )
        except Exception:
            return False

    def __getitem__(self, key: _ResolvableKeyT) -> _ValueT:
        return self._values[self._key_resolver(key)]

    def __delitem__(self, key: _ResolvableKeyT) -> None:
        del self._values[self._key_resolver(key)]

    def clear(self) -> None:
        """
        Remove all values from the collection.
        """
        self._values.clear()

    def add(self, *values: _ResolvableValueT) -> None:
        """
        Add a value to the collection.
        """
        # Resolve the values, so the collection resolver won't have to and can stay small.
        resolved_values = list(map(self._value_resolver, values))
        # Allow the collection resolver to change the collection or raise (validation) errors.
        twice_resolved_values = self._resolver(resolved_values)
        # Resolve the values again, so the collection resolver won't have to and can stay small.
        thrice_resolved_values = list(map(self._value_resolver, twice_resolved_values))  # ty:ignore[invalid-argument-type]
        for value in thrice_resolved_values:
            self._values[self._key(value)] = value

    def keys(self) -> Iterable[_KeyT]:
        """
        Get an iterable over the collection's keys.
        """
        return self._values.keys()


@final
class ResolvingMutableSequence(
    MutableSequence[_ValueT], Generic[_ValueT, _ResolvableValueT]
):
    """
    A sequence of values.
    """

    def __init__(
        self,
        decorated: MutableSequence[_ValueT],
        resolver: Callable[[_ResolvableValueT | _ValueT], _ValueT],
        /,
    ):
        self._decorated = decorated
        self._resolver = resolver

    @override
    def insert(self, index: int, value: _ResolvableValueT | _ValueT) -> None:
        self._decorated.insert(index, self._resolver(value))

    @overload
    def __getitem__(self, index: int) -> _ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[_ValueT]:
        pass

    def __getitem__(self, index):
        return self._decorated[index]

    @overload
    def __setitem__(self, index: int, value: _ResolvableValueT | _ValueT) -> None: ...

    @overload
    def __setitem__(
        self, index: slice, value: Iterable[_ResolvableValueT | _ValueT]
    ) -> None: ...

    def __setitem__(self, index, value):
        if isinstance(index, int):
            self._decorated[index] = self._resolver(value)
        else:
            self._decorated[index] = map(self._resolver, value)

    def __delitem__(self, index: int | slice) -> None:
        del self._decorated[index]

    def __len__(self):
        return len(self._decorated)

    def __contains__(self, value: object) -> bool:
        try:
            return (
                self._resolver(
                    value,  # ty:ignore[invalid-argument-type]
                )
                in self._decorated
            )
        except Exception:
            return False

    @override
    def extend(self, values: Iterable[_ValueT | _ResolvableValueT]) -> None:
        self._decorated.extend(map(self._resolver, values))
