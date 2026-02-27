"""
Keyed collection proxies.
"""

from collections.abc import Iterable, Iterator
from typing import Any, override

from betty.collection.keyed import KeyedCollection, MutableKeyedCollection


class _KeyedCollectionProxy[
    KeyT,
    ResolvableKeyT,
    ValueT,
    KeyedCollectionT: KeyedCollection,
](KeyedCollection[KeyT, ResolvableKeyT, ValueT]):
    def __init__(self, upstream: KeyedCollectionT, /):
        self._upstream = upstream

    @override
    def __len__(self) -> int:
        return len(self._upstream)

    @override
    def __iter__(self) -> Iterator[ValueT]:
        return iter(self._upstream)

    @override
    def __contains__(self, key: Any) -> bool:
        return key in self._upstream

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._upstream[key]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self._upstream.keys()


class KeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT](
    _KeyedCollectionProxy[
        KeyT, ResolvableKeyT, ValueT, KeyedCollection[KeyT, ResolvableKeyT, ValueT]
    ]
):
    """
    A keyed collection proxy.
    """


class MutableKeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _KeyedCollectionProxy[
        KeyT,
        ResolvableKeyT,
        ValueT,
        MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
    ],
    MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable keyed collection proxy.
    """

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        self._upstream.remove(*keys)

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._upstream[key]

    @override
    def clear(self) -> None:
        self._upstream.clear()

    @override
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        self._upstream.add(*values)
