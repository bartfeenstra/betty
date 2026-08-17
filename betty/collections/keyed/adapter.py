"""
Adapters between keyed collections and Python data types.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, override

from betty.collection.keyed import KeyedCollection, MutableKeyedCollection
from betty.collections import _empty_frozen_mapping
from betty.functools import passthrough

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping


class KeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT](
    KeyedCollection[KeyT, ResolvableKeyT, ValueT]
):
    """
    A collection of values that are accessible by their primary keys.
    """

    def __init__(
        self,
        values: Mapping[KeyT, ValueT]
        | Iterable[tuple[KeyT, ValueT]] = _empty_frozen_mapping,
        *,
        key_resolver: Callable[[ResolvableKeyT | KeyT], KeyT] = passthrough,
    ):
        self._values = dict(values)
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


class MutableKeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    KeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT],
    MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable ordered collection of values that are accessible by their primary keys.
    """

    def __init__(
        self,
        values: Iterable[ResolvableValueT] = (),
        *,
        key: Callable[[ValueT], KeyT],
        key_resolver: Callable[[ResolvableKeyT | KeyT], KeyT] = passthrough,
        value_resolver: Callable[[ResolvableValueT | ValueT], ValueT] = passthrough,
    ):
        super().__init__(key_resolver=key_resolver)
        self._key = key
        self._value_resolver = value_resolver
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
            self._value_resolver,
            values,
        ):
            self._values[self._key(value)] = value
