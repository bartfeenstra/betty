"""
Collection data tpes.
"""

from abc import abstractmethod
from collections.abc import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from contextlib import suppress
from itertools import chain
from typing import Any, Generic, TypeVar, final, overload

from typing_extensions import override

from betty.functools import passthrough
from betty.typing import Void

_T = TypeVar("_T")
_KeyT = TypeVar("_KeyT")
_ValueT = TypeVar("_ValueT")
_ResolvableKeyT = TypeVar("_ResolvableKeyT")
_ResolvableValueT = TypeVar("_ResolvableValueT")


class MutableCollection(Collection[_ValueT]):
    """
    A mutable collection of values.
    """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """


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


class ResolvedMapping(
    Mapping[_KeyT, _ValueT], Generic[_KeyT, _ResolvableKeyT, _ValueT]
):
    """
    A mutable mapping of resolved keys.
    """

    @override
    @abstractmethod
    def __getitem__(self, key: _KeyT | _ResolvableKeyT) -> _ValueT:
        pass

    @overload
    def get(self, key: _KeyT | _ResolvableKeyT, default: _T, /) -> _ValueT | _T:
        pass

    @overload
    def get(
        self, key: _KeyT | _ResolvableKeyT, default: None = None, /
    ) -> _ValueT | None:
        pass

    @override
    @abstractmethod
    def get(
        self, key: _KeyT | _ResolvableKeyT, default: _T | None = None, /
    ) -> _ValueT | None:
        pass


class MutableResolvedMapping(
    MutableMapping[_KeyT, _ValueT],
    MutableCollection[_KeyT],
    ResolvedMapping[_KeyT, _ResolvableKeyT, _ValueT],
    Generic[_KeyT, _ResolvableKeyT, _ValueT, _ResolvableValueT],
):
    """
    A mutable mapping of resolved keys and values.
    """

    @abstractmethod
    def __setitem__(
        self, key: _KeyT | _ResolvableKeyT, value: _ValueT | _ResolvableValueT
    ) -> None:
        pass

    @abstractmethod
    def __delitem__(self, key: _KeyT | _ResolvableKeyT) -> None:
        pass

    @overload
    def update(
        self,
        other: Mapping[_KeyT | _ResolvableKeyT, _ValueT | _ResolvableValueT]
        | Iterable[tuple[_KeyT | _ResolvableKeyT, _ValueT | _ResolvableValueT]],
        /,
        **kwargs: _ValueT | _ResolvableValueT,
    ) -> None:
        pass

    @overload
    def update(self, **kwargs: _ValueT | _ResolvableValueT) -> None:
        pass

    @override
    @abstractmethod
    def update(self, other=None, **kwargs) -> None:  # ty:ignore[invalid-method-override]
        pass

    @overload
    def setdefault(
        self: MutableMapping[_KeyT, _T | None],
        key: _KeyT | _ResolvableKeyT,
        default: None = None,
        /,
    ) -> _T | None:
        pass

    @overload
    def setdefault(
        self, key: _KeyT | _ResolvableKeyT, default: _ValueT | _ResolvableValueT, /
    ) -> _ValueT:
        pass

    @override
    @abstractmethod
    def setdefault(self, key, default):
        pass

    @overload
    def pop(self, key: _KeyT | _ResolvableKeyT, /) -> _ValueT:
        pass

    @overload
    def pop(
        self, key: _KeyT | _ResolvableKeyT, /, default: _ValueT | _ResolvableValueT
    ) -> _ValueT:
        pass

    @overload
    def pop(self, key: _KeyT | _ResolvableKeyT, /, default: _T) -> _ValueT | _T:
        pass

    @override
    @abstractmethod
    def pop(self, key, default):
        pass

    @override
    @abstractmethod
    def popitem(self) -> tuple[_KeyT, _ValueT]:
        pass


class _ResolvedMappingProxy(ResolvedMapping[_KeyT, _ResolvableKeyT, _ValueT]):
    def __init__(
        self,
        upstream: Mapping[_KeyT, _ValueT],
        *,
        key_resolver: Callable[[_KeyT | _ResolvableKeyT], _KeyT] = passthrough,
    ):
        self._upstream = upstream
        self._key_resolver = key_resolver

    @final
    @override
    def __getitem__(self, key: _KeyT | _ResolvableKeyT) -> _ValueT:
        return self._upstream[self._key_resolver(key)]

    @overload
    def get(self, key: _KeyT | _ResolvableKeyT, default: _T, /) -> _ValueT | _T:
        pass

    @overload
    def get(
        self, key: _KeyT | _ResolvableKeyT, default: None = None, /
    ) -> _ValueT | None:
        pass

    @final
    @override
    def get(self, key, default=None):
        return self._upstream.get(self._key_resolver(key), default)

    @final
    @override
    def __iter__(self) -> Iterator[_KeyT]:
        return iter(self._upstream)

    @final
    @override
    def __len__(self) -> int:
        return len(self._upstream)

    @final
    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self._key_resolver(key)
        return key in self._upstream


@final
class ResolvedMappingProxy(_ResolvedMappingProxy[_KeyT, _ResolvableKeyT, _ValueT]):
    """
    Decorate another mapping to resolve any values before proxying them.
    """


@final
class MutableResolvedMappingProxy(
    _ResolvedMappingProxy[_KeyT, _ResolvableKeyT, _ValueT],
    MutableResolvedMapping[_KeyT, _ResolvableKeyT, _ValueT, _ResolvableValueT],
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    _upstream: MutableMapping[_KeyT, _ValueT]

    def __init__(
        self,
        upstream: MutableMapping[_KeyT, _ValueT],
        *,
        key_resolver: Callable[[_KeyT | _ResolvableKeyT], _KeyT] = passthrough,
        value_resolver: Callable[[_ValueT | _ResolvableValueT], _ValueT] = passthrough,
    ):
        super().__init__(upstream, key_resolver=key_resolver)
        self._value_resolver = value_resolver

    def __setitem__(
        self, key: _KeyT | _ResolvableKeyT, value: _ValueT | _ResolvableValueT
    ) -> None:
        self._upstream[self._key_resolver(key)] = self._value_resolver(value)

    def __delitem__(self, key: _KeyT | _ResolvableKeyT) -> None:
        del self._upstream[self._key_resolver(key)]

    @overload
    def update(
        self,
        other: Mapping[_KeyT | _ResolvableKeyT, _ValueT | _ResolvableValueT]
        | Iterable[tuple[_KeyT | _ResolvableKeyT, _ValueT | _ResolvableValueT]],
        /,
        **kwargs: _ValueT | _ResolvableValueT,
    ) -> None:
        pass

    @overload
    def update(self, **kwargs: _ValueT | _ResolvableValueT) -> None:
        pass

    @override
    def update(self, other=None, **kwargs) -> None:
        items = kwargs.items()
        if isinstance(other, Mapping):
            items = chain(items, other.items())
        elif isinstance(other, Sequence):
            items = chain(items, other)
        self._upstream.update(
            {
                self._key_resolver(key): self._value_resolver(value)  # ty:ignore[invalid-argument-type]
                for key, value in items
            }
        )

    @overload
    def setdefault(
        self: MutableMapping[_KeyT, _T | None],
        key: _KeyT | _ResolvableKeyT,
        default: None = None,
        /,
    ) -> _T | None:
        pass

    @overload
    def setdefault(
        self, key: _KeyT | _ResolvableKeyT, default: _ValueT | _ResolvableValueT, /
    ) -> _ValueT:
        pass

    @override
    def setdefault(
        self,
        key,
        default=Void(),  # noqa: B008
    ):
        return self._upstream.setdefault(
            self._key_resolver(key),
            None if default is Void() else self._value_resolver(default),  # ty:ignore[invalid-argument-type]
        )  # ty:ignore[no-matching-overload]

    @overload
    def pop(self, key: _KeyT | _ResolvableKeyT, /) -> _ValueT:
        pass

    @overload
    def pop(
        self, key: _KeyT | _ResolvableKeyT, /, default: _ValueT | _ResolvableValueT
    ) -> _ValueT:
        pass

    @overload
    def pop(self, key: _KeyT | _ResolvableKeyT, /, default: _T) -> _ValueT | _T:
        pass

    @override
    def pop(
        self,
        key,
        default=Void(),  # noqa: B008
    ):
        key = self._key_resolver(key)
        if default is Void():
            return self._upstream.pop(key)
        return self._upstream.pop(key, default)

    @override
    def popitem(self) -> tuple[_KeyT, _ValueT]:
        return self._upstream.popitem()


class AutoMapping(
    ResolvedMapping[_KeyT, _ResolvableKeyT, _ValueT],
    MutableCollection[_ValueT],
    Generic[_KeyT, _ResolvableKeyT, _ValueT, _ResolvableValueT],
):
    """
    A mutable mapping of values that are automatically keyed.
    """

    @abstractmethod
    def add(self, *values: _ValueT | _ResolvableValueT) -> None:
        """
        Add one or more values to the mapping.
        """

    @abstractmethod
    def remove(self, *keys: _KeyT | _ResolvableKeyT) -> None:
        """
        Remove one or more keys from the mapping.
        """

    @abstractmethod
    def __delitem__(self, key: _KeyT | _ResolvableKeyT) -> None:
        pass


@final
class AutoDict(
    _ResolvedMappingProxy[_KeyT, _ResolvableKeyT, _ValueT],
    AutoMapping[_KeyT, _ResolvableKeyT, _ValueT, _ResolvableValueT],
):
    """
    A mutable mapping of values that are automatically keyed, backed by a dictionary.
    """

    _upstream: MutableMapping[_KeyT, _ValueT]

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
        super().__init__({}, key_resolver=key_resolver)
        self._key = key
        self._value_resolver = value_resolver
        self._resolver = resolver
        if values is not None:
            self.add(*values)

    @override
    def keys(self) -> KeysView[_KeyT]:
        return self._upstream.keys()

    @override
    def remove(self, *keys: _KeyT | _ResolvableKeyT) -> None:
        for key in keys:
            del self[key]

    @override
    def __delitem__(self, key: _KeyT | _ResolvableKeyT) -> None:
        del self._upstream[self._key_resolver(key)]

    @override
    def clear(self) -> None:
        self._upstream.clear()

    @override
    def add(self, *values: _ValueT | _ResolvableValueT) -> None:
        # Resolve the values, so the collection resolver won't have to and can stay small.
        resolved_values = list(map(self._value_resolver, values))
        # Allow the collection resolver to change the collection or raise (validation) errors.
        twice_resolved_values = self._resolver(resolved_values)
        # Resolve the values again, so the collection resolver won't have to and can stay small.
        thrice_resolved_values = list(map(self._value_resolver, twice_resolved_values))  # ty:ignore[invalid-argument-type]
        for value in thrice_resolved_values:
            self._upstream[self._key(value)] = value
