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
    MutableMapping,
    MutableSequence,
    Sequence,
)
from contextlib import suppress
from itertools import chain
from typing import Any, final, overload, override

from betty.functools import passthrough
from betty.typing import Void


class KeyedCollection[KeyT, ResolvableKeyT, ValueT](Collection[ValueT]):
    """
    A collection of values that are accessible by their primary keys.
    """

    @abstractmethod
    def keys(self) -> Iterable[KeyT]:
        """
        Get an iterable over the collection's primary keys.
        """

    @abstractmethod
    def __getitem__(self, key: ResolvableKeyT) -> ValueT:
        pass


class MutableCollection[ValueT](Collection[ValueT]):
    """
    A mutable collection of values.
    """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """


class MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    KeyedCollection[KeyT, ResolvableKeyT, ValueT],
    MutableCollection[ValueT],
):
    """
    A mutable collection of values that are accessible by their primary keys.
    """

    @abstractmethod
    def add(self, *values: ResolvableValueT) -> None:
        """
        Add a value to the collection.
        """

    @abstractmethod
    def __delitem__(self, key: ResolvableKeyT) -> None:
        pass


class _DictKeyedCollection[KeyT, ResolvableKeyT, ValueT](
    KeyedCollection[KeyT, ResolvableKeyT, ValueT]
):
    def __init__(
        self,
        values: Mapping[KeyT, ValueT] | None = None,
        *,
        key_resolver: Callable[[ResolvableKeyT | KeyT], KeyT] = passthrough,
    ):
        self._values = {} if values is None else dict(values)
        self._key_resolver = key_resolver

    @override
    def __len__(self) -> int:
        return self._values.__len__()

    @override
    def __iter__(self) -> Iterator[ValueT]:
        yield from self._values.values()

    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self._key_resolver(key)
        return key in self._values

    @override
    def __getitem__(self, key: ResolvableKeyT) -> ValueT:
        return self._values[self._key_resolver(key)]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self._values.keys()


@final
class DictKeyedCollection[KeyT, ResolvableKeyT, ValueT](
    _DictKeyedCollection[KeyT, ResolvableKeyT, ValueT]
):
    """
    A keyed collection backed by a dictionary.
    """


@final
class MutableDictKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _DictKeyedCollection[KeyT, ResolvableKeyT, ValueT],
    MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable keyed collection backed by a dictionary.
    """

    def __init__(
        self,
        values: Iterable[ResolvableValueT] | None = None,
        *,
        key: Callable[[ValueT], KeyT],
        key_resolver: Callable[[ResolvableKeyT | KeyT], KeyT] = passthrough,
        value_resolver: Callable[[ResolvableValueT | KeyT], ValueT] = passthrough,
        resolver: Callable[
            [Sequence[ValueT]], Sequence[ValueT | ResolvableValueT]
        ] = passthrough,
    ):
        super().__init__(key_resolver=key_resolver)
        self._key = key
        self._value_resolver = value_resolver
        self._resolver = resolver
        if values is not None:
            self.add(*values)

    @override
    def __delitem__(self, key: ResolvableKeyT) -> None:
        del self._values[self._key_resolver(key)]

    @override
    def clear(self) -> None:
        self._values.clear()

    @override
    def add(self, *values: ResolvableValueT) -> None:
        # Resolve the values, so the collection resolver won't have to and can stay small.
        resolved_values = list(map(self._value_resolver, values))
        # Allow the collection resolver to change the collection or raise (validation) errors.
        twice_resolved_values = self._resolver(resolved_values)
        # Resolve the values again, so the collection resolver won't have to and can stay small.
        thrice_resolved_values = list(map(self._value_resolver, twice_resolved_values))  # ty:ignore[invalid-argument-type]
        for value in thrice_resolved_values:
            self._values[self._key(value)] = value


class MutableResolvedSequence[ValueT, ResolvableValueT](
    MutableSequence[ValueT],
    MutableCollection[ValueT],
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


class _ResolvedSequenceProxy[ValueT, ResolvableValueT](Sequence[ValueT]):
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
class ResolvedSequenceProxy[ValueT, ResolvableValueT](
    _ResolvedSequenceProxy[ValueT, ResolvableValueT]
):
    """
    Decorate another sequence to resolve any values before proxying them.
    """


@final
class MutableResolvedSequenceProxy[ValueT, ResolvableValueT](
    _ResolvedSequenceProxy[ValueT, ResolvableValueT],
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


class ResolvedMapping[KeyT, ResolvableKeyT, ValueT](Mapping[KeyT, ValueT]):
    """
    A mutable mapping of resolved keys.
    """

    @override
    @abstractmethod
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        pass

    @overload
    def get[T](self, key: KeyT | ResolvableKeyT, default: T, /) -> ValueT | T:
        pass

    @overload
    def get(self, key: KeyT | ResolvableKeyT, default: None = None, /) -> ValueT | None:
        pass

    @override
    @abstractmethod
    def get[T](
        self, key: KeyT | ResolvableKeyT, default: T | None = None, /
    ) -> ValueT | None:
        pass


class MutableResolvedMapping[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableMapping[KeyT, ValueT],
    MutableCollection[KeyT],
    ResolvedMapping[KeyT, ResolvableKeyT, ValueT],
):
    """
    A mutable mapping of resolved keys and values.
    """

    @abstractmethod
    def __setitem__(
        self, key: KeyT | ResolvableKeyT, value: ValueT | ResolvableValueT
    ) -> None:
        pass

    @abstractmethod
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        pass

    @overload
    def update(
        self,
        other: Mapping[KeyT | ResolvableKeyT, ValueT | ResolvableValueT]
        | Iterable[tuple[KeyT | ResolvableKeyT, ValueT | ResolvableValueT]],
        /,
        **kwargs: ValueT | ResolvableValueT,
    ) -> None:
        pass

    @overload
    def update(self, **kwargs: ValueT | ResolvableValueT) -> None:
        pass

    @override
    @abstractmethod
    def update(self, other=None, **kwargs) -> None:  # ty:ignore[invalid-method-override]
        pass

    @overload
    def setdefault[T](
        self: MutableMapping[KeyT, T | None],
        key: KeyT | ResolvableKeyT,
        default: None = None,
        /,
    ) -> T | None:
        pass

    @overload
    def setdefault[T](
        self, key: KeyT | ResolvableKeyT, default: ValueT | ResolvableValueT, /
    ) -> ValueT:
        pass

    @override
    @abstractmethod
    def setdefault(self, key, default):
        pass

    @overload
    def pop(self, key: KeyT | ResolvableKeyT, /) -> ValueT:
        pass

    @overload
    def pop(
        self, key: KeyT | ResolvableKeyT, /, default: ValueT | ResolvableValueT
    ) -> ValueT:
        pass

    @overload
    def pop[T](self, key: KeyT | ResolvableKeyT, /, default: T) -> ValueT | T:
        pass

    @override
    @abstractmethod
    def pop(self, key, default):
        pass

    @override
    @abstractmethod
    def popitem(self) -> tuple[KeyT, ValueT]:
        pass


class _ResolvedMappingProxy[KeyT, ResolvableKeyT, ValueT](
    ResolvedMapping[KeyT, ResolvableKeyT, ValueT]
):
    def __init__(
        self,
        upstream: Mapping[KeyT, ValueT],
        *,
        key_resolver: Callable[[KeyT | ResolvableKeyT], KeyT] = passthrough,
    ):
        self._upstream = upstream
        self._key_resolver = key_resolver

    @final
    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._upstream[self._key_resolver(key)]

    @overload
    def get[T](self, key: KeyT | ResolvableKeyT, default: T, /) -> ValueT | T:
        pass

    @overload
    def get(self, key: KeyT | ResolvableKeyT, default: None = None, /) -> ValueT | None:
        pass

    @final
    @override
    def get(self, key, default=None):
        return self._upstream.get(self._key_resolver(key), default)

    @final
    @override
    def __iter__(self) -> Iterator[KeyT]:
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
class ResolvedMappingProxy[KeyT, ResolvableKeyT, ValueT](
    _ResolvedMappingProxy[KeyT, ResolvableKeyT, ValueT]
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """


@final
class MutableResolvedMappingProxy[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _ResolvedMappingProxy[KeyT, ResolvableKeyT, ValueT],
    MutableResolvedMapping[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    _upstream: MutableMapping[KeyT, ValueT]

    def __init__(
        self,
        upstream: MutableMapping[KeyT, ValueT],
        *,
        key_resolver: Callable[[KeyT | ResolvableKeyT], KeyT] = passthrough,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT] = passthrough,
    ):
        super().__init__(upstream, key_resolver=key_resolver)
        self._value_resolver = value_resolver

    def __setitem__(
        self, key: KeyT | ResolvableKeyT, value: ValueT | ResolvableValueT
    ) -> None:
        self._upstream[self._key_resolver(key)] = self._value_resolver(value)

    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._upstream[self._key_resolver(key)]

    @overload
    def update(
        self,
        other: Mapping[KeyT | ResolvableKeyT, ValueT | ResolvableValueT]
        | Iterable[tuple[KeyT | ResolvableKeyT, ValueT | ResolvableValueT]],
        /,
        **kwargs: ValueT | ResolvableValueT,
    ) -> None:
        pass

    @overload
    def update(self, **kwargs: ValueT | ResolvableValueT) -> None:
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
    def setdefault[T](
        self: MutableMapping[KeyT, T | None],
        key: KeyT | ResolvableKeyT,
        default: None = None,
        /,
    ) -> T | None:
        pass

    @overload
    def setdefault(
        self, key: KeyT | ResolvableKeyT, default: ValueT | ResolvableValueT, /
    ) -> ValueT:
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
    def pop(self, key: KeyT | ResolvableKeyT, /) -> ValueT:
        pass

    @overload
    def pop(
        self, key: KeyT | ResolvableKeyT, /, default: ValueT | ResolvableValueT
    ) -> ValueT:
        pass

    @overload
    def pop[T](self, key: KeyT | ResolvableKeyT, /, default: T) -> ValueT | T:
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
    def popitem(self) -> tuple[KeyT, ValueT]:
        return self._upstream.popitem()
