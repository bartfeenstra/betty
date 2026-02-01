"""
Collection data tpes.
"""

from abc import abstractmethod
from collections.abc import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    MutableSequence,
    Sequence,
)
from contextlib import suppress
from typing import Any, Generic, TypeVar, final, overload

from typing_extensions import override

from betty.functools import passthrough

_KeyT = TypeVar("_KeyT")
_ValueT = TypeVar("_ValueT")
_ResolvableKeyT = TypeVar("_ResolvableKeyT")
_ResolvableValueT = TypeVar("_ResolvableValueT")


class KeyedCollection(Collection[_ValueT], Generic[_KeyT, _ResolvableKeyT, _ValueT]):
    """
    A collection of values that are accessible by their primary keys.
    """

    @abstractmethod
    def keys(self) -> Iterable[_KeyT]:
        """
        Get an iterable over the collection's primary keys.
        """

    @abstractmethod
    def __getitem__(self, key: _ResolvableKeyT) -> _ValueT:
        pass


class MutableCollection(Collection[_ValueT]):
    """
    A mutable collection of values.
    """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """


class MutableKeyedCollection(
    KeyedCollection[_KeyT, _ResolvableKeyT, _ValueT],
    MutableCollection[_ValueT],
    Generic[_KeyT, _ResolvableKeyT, _ValueT, _ResolvableValueT],
):
    """
    A mutable collection of values that are accessible by their primary keys.
    """

    @abstractmethod
    def add(self, *values: _ResolvableValueT) -> None:
        """
        Add a value to the collection.
        """

    @abstractmethod
    def __delitem__(self, key: _ResolvableKeyT) -> None:
        pass


class _DictKeyedCollection(KeyedCollection[_KeyT, _ResolvableKeyT, _ValueT]):
    def __init__(
        self,
        values: Mapping[_KeyT, _ValueT] | None = None,
        *,
        key_resolver: Callable[[_ResolvableKeyT | _KeyT], _KeyT] = passthrough,
    ):
        self._values = {} if values is None else dict(values)
        self._key_resolver = key_resolver

    @override
    def __len__(self) -> int:
        return self._values.__len__()

    @override
    def __iter__(self) -> Iterator[_ValueT]:
        yield from self._values.values()

    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self._key_resolver(key)
        return key in self._values

    @override
    def __getitem__(self, key: _ResolvableKeyT) -> _ValueT:
        return self._values[self._key_resolver(key)]

    @override
    def keys(self) -> Iterable[_KeyT]:
        return self._values.keys()


@final
class DictKeyedCollection(_DictKeyedCollection[_KeyT, _ResolvableKeyT, _ValueT]):
    """
    A keyed collection backed by a dictionary.
    """


@final
class MutableDictKeyedCollection(
    _DictKeyedCollection[_KeyT, _ResolvableKeyT, _ValueT],
    MutableKeyedCollection[_KeyT, _ResolvableKeyT, _ValueT, _ResolvableValueT],
):
    """
    A mutable keyed collection backed by a dictionary.
    """

    def __init__(
        self,
        values: Iterable[_ResolvableValueT] | None = None,
        *,
        key: Callable[[_ValueT], _KeyT],
        key_resolver: Callable[[_ResolvableKeyT | _KeyT], _KeyT] = passthrough,
        value_resolver: Callable[[_ResolvableValueT | _KeyT], _ValueT] = passthrough,
        resolver: Callable[
            [Sequence[_ValueT]], Sequence[_ValueT | _ResolvableValueT]
        ] = passthrough,
    ):
        super().__init__(key_resolver=key_resolver)
        self._key = key
        self._value_resolver = value_resolver
        self._resolver = resolver
        if values is not None:
            self.add(*values)

    @override
    def __delitem__(self, key: _ResolvableKeyT) -> None:
        del self._values[self._key_resolver(key)]

    @override
    def clear(self) -> None:
        self._values.clear()

    @override
    def add(self, *values: _ResolvableValueT) -> None:
        # Resolve the values, so the collection resolver won't have to and can stay small.
        resolved_values = list(map(self._value_resolver, values))
        # Allow the collection resolver to change the collection or raise (validation) errors.
        twice_resolved_values = self._resolver(resolved_values)
        # Resolve the values again, so the collection resolver won't have to and can stay small.
        thrice_resolved_values = list(map(self._value_resolver, twice_resolved_values))  # ty:ignore[invalid-argument-type]
        for value in thrice_resolved_values:
            self._values[self._key(value)] = value


class MutableResolvedSequence(
    MutableSequence[_ValueT],
    MutableCollection[_ValueT],
    Generic[_ValueT, _ResolvableValueT],
):
    """
    A mutable sequence of resolved values.
    """

    @override
    @abstractmethod
    def insert(self, index: int, value: _ValueT | _ResolvableValueT) -> None:
        pass

    @overload
    def __setitem__(self, index: int, value: _ValueT | _ResolvableValueT) -> None:
        pass

    @overload
    def __setitem__(
        self, index: slice, value: Iterable[_ValueT | _ResolvableValueT]
    ) -> None:
        pass

    @abstractmethod
    def __setitem__(self, index, value):
        pass

    @override
    @abstractmethod
    def extend(self, values: Iterable[_ValueT | _ResolvableValueT]) -> None:
        pass


class _ResolvedSequenceProxy(Sequence[_ValueT], Generic[_ValueT, _ResolvableValueT]):
    def __init__(
        self,
        upstream: Sequence[_ValueT],
        *,
        value_resolver: Callable[[_ValueT | _ResolvableValueT], _ValueT],
    ):
        self._upstream = upstream
        self._value_resolver = value_resolver

    @overload
    def __getitem__(self, index: int) -> _ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[_ValueT]:
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
class ResolvedSequenceProxy(_ResolvedSequenceProxy[_ValueT, _ResolvableValueT]):
    """
    Decorate another sequence to resolve any values before proxying them.
    """


@final
class MutableResolvedSequenceProxy(
    _ResolvedSequenceProxy[_ValueT, _ResolvableValueT],
    MutableResolvedSequence[_ValueT, _ResolvableValueT],
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """

    _upstream: MutableSequence[_ValueT]

    def __init__(
        self,
        upstream: MutableSequence[_ValueT],
        *,
        value_resolver: Callable[[_ValueT | _ResolvableValueT], _ValueT],
    ):
        super().__init__(upstream, value_resolver=value_resolver)

    @override
    def insert(self, index: int, value: _ValueT | _ResolvableValueT) -> None:
        self._upstream.insert(index, self._value_resolver(value))

    @overload
    def __setitem__(self, index: int, value: _ValueT | _ResolvableValueT) -> None:
        pass

    @overload
    def __setitem__(
        self, index: slice, value: Iterable[_ValueT | _ResolvableValueT]
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
    def extend(self, values: Iterable[_ValueT | _ResolvableValueT]) -> None:
        self._upstream.extend(map(self._value_resolver, values))
