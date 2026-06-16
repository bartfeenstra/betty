"""
Keyed collection proxies.
"""

from collections.abc import Iterable, Iterator
from typing import Any, override

from betty.collection.keyed import KeyedCollection, MutableKeyedCollection


class KeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT](
    KeyedCollection[KeyT, ResolvableKeyT, ValueT]
):
    """
    A keyed collection proxy.
    """

    def __init__(self, proxied: KeyedCollection[KeyT, ResolvableKeyT, ValueT], /):
        self._proxied = proxied

    @override
    def __len__(self) -> int:
        return len(self._proxied)

    @override
    def __iter__(self) -> Iterator[ValueT]:
        return iter(self._proxied)

    @override
    def __contains__(self, key: Any) -> bool:
        return key in self._proxied

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._proxied[key]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self._proxied.keys()


class MutableKeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    KeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT],
    MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable keyed collection proxy.
    """

    _proxied: MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT]

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        self._proxied.remove(*keys)

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._proxied[key]

    @override
    def clear(self) -> None:
        self._proxied.clear()

    @override
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        self._proxied.add(*values)
