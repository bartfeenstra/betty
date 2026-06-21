"""
Keyed collection proxies that raise custom errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.collection.keyed.proxy import (
    KeyedCollectionProxy,
    MutableKeyedCollectionProxy,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.collection.keyed import KeyedCollection, MutableKeyedCollection


class ErroringKeyedCollection[KeyT, ResolvableKeyT, ValueT](
    KeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT]
):
    """
    A keyed collection proxy that raises custom errors.
    """

    def __init__(
        self,
        proxied: KeyedCollection[KeyT, ResolvableKeyT, ValueT],
        key_error: Callable[[KeyError, KeyT | ResolvableKeyT], KeyError],
        /,
    ):
        super().__init__(proxied)
        self._key_error = key_error

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        try:
            return self._proxied[key]
        except KeyError as error:
            raise self._key_error(error, key) from error


class MutableErroringKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    ErroringKeyedCollection[KeyT, ResolvableKeyT, ValueT],
    MutableKeyedCollectionProxy[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable keyed collection proxy that raises custom errors.
    """

    _proxied: MutableKeyedCollection[KeyT, ResolvableKeyT, ValueT, ResolvableValueT]

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        for key in keys:
            try:
                self._proxied.remove(key)
            except KeyError as error:
                raise self._key_error(error, key) from error

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        try:
            del self._proxied[key]
        except KeyError as error:
            raise self._key_error(error, key) from error
