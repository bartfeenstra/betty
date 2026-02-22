"""
Adapters between keyed collections and Python data types.
"""

from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import suppress
from typing import Any, final, override

from betty.collection.keyed import KeyedCollection, MutableKeyedCollection
from betty.functools import passthrough


class _KeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT](
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
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._values[self._key_resolver(key)]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self._values.keys()


@final
class KeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT](
    _KeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT]
):
    """
    A collection of values that are accessible by their primary keys.
    """


@final
class MutableKeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _KeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT],
    MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable ordered collection of values that are accessible by their primary keys.
    """

    def __init__(
        self,
        values: Iterable[ResolvableValueT] | None = None,
        *,
        key: Callable[[ValueT], KeyT],
        key_resolver: Callable[[ResolvableKeyT | KeyT], KeyT] = passthrough,
        value_resolver: Callable[[ResolvableValueT | KeyT], ValueT] = passthrough,
    ):
        super().__init__(key_resolver=key_resolver)
        self._key = key
        self._value_resolver = value_resolver
        if values is not None:
            self.add(*values)

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        for key in keys:
            del self[key]

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._values[self._key_resolver(key)]

    @override
    def clear(self) -> None:
        self._values.clear()

    @override
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        for value in map(
            self._value_resolver,  # ty:ignore[invalid-argument-type]
            values,
        ):
            self._values[self._key(value)] = value
