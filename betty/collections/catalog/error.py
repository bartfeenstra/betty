"""
Catalog proxies that raise custom errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.collections.catalog.proxy import CatalogProxy, MutableCatalogProxy

if TYPE_CHECKING:
    from collections.abc import Callable

    from ty_extensions import Intersection

    from betty.collection.catalog import Catalog, MutableCatalog


class ErroringCatalog[KeyT, ResolvableKeyT, ValueT, WrappedT: Catalog](
    CatalogProxy[KeyT, ResolvableKeyT, ValueT, WrappedT]
):
    """
    A catalog proxy that raises custom errors.
    """

    def __init__(
        self,
        wrapped: Intersection[WrappedT, Catalog[KeyT, ResolvableKeyT, ValueT]],
        key_error: Callable[[KeyError, KeyT | ResolvableKeyT], KeyError],
        /,
    ):
        super().__init__(wrapped)
        self._key_error = key_error

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        try:
            return self.__wrapped__[key]
        except KeyError as error:
            raise self._key_error(error, key) from error


class MutableErroringCatalog[
    KeyT,
    ResolvableKeyT,
    ValueT,
    ResolvableValueT,
    WrappedT: MutableCatalog,
](
    ErroringCatalog[KeyT, ResolvableKeyT, ValueT, WrappedT],
    MutableCatalogProxy[KeyT, ResolvableKeyT, ValueT, ResolvableValueT, WrappedT],
):
    """
    A mutable catalog proxy that raises custom errors.
    """

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        for key in keys:
            try:
                self.__wrapped__.remove(key)
            except KeyError as error:
                raise self._key_error(error, key) from error

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        try:
            del self.__wrapped__[key]
        except KeyError as error:
            raise self._key_error(error, key) from error
