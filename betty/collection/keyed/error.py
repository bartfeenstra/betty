"""
Keyed collection proxies that raise custom errors.
"""

from collections.abc import Callable
from typing import final, override

from betty.collection.keyed import KeyedCollection, MutableKeyedCollection
from betty.collection.keyed.proxy import (
    KeyedCollectionProxy,
    MutableKeyedCollectionProxy,
)


class _ErroringKeyedCollection[
    KeyT,
    ResolvableKeyT,
    ValueT,
    KeyedCollectionT: KeyedCollection,
](KeyedCollection[KeyT, ResolvableKeyT, ValueT]):
    def __init__(
        self,
        upstream: KeyedCollection[KeyT, ResolvableKeyT, ValueT],
        key_error: Callable[[KeyError, KeyT | ResolvableKeyT], KeyError],
        /,
    ):
        super().__init__(upstream)
        self._key_error = key_error


@final
class ErroringKeyedCollection[KeyT, ResolvableKeyT, ValueT](
    _ErroringKeyedCollection[
        KeyT, ResolvableKeyT, ValueT, KeyedCollection[KeyT, ResolvableKeyT, ValueT]
    ],
    KeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT],
):
    """
    A keyed collection proxy that raises custom errors.
    """

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        try:
            return self._upstream[key]
        except KeyError as error:
            raise self._key_error(error, key) from error


@final
class MutableErroringKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _ErroringKeyedCollection[
        KeyT,
        ResolvableKeyT,
        ValueT,
        MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
    ],
    MutableKeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable keyed collection proxy that raises custom errors.
    """

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        for key in keys:
            try:
                self._upstream.remove(key)
            except KeyError as error:
                raise self._key_error(error, key) from error

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        try:
            del self._upstream[key]
        except KeyError as error:
            raise self._key_error(error, key) from error
