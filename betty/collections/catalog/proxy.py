"""
Catalog proxies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.collection.catalog import Catalog, MutableCatalog

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from ty_extensions import Intersection


class CatalogProxy[KeyT, ResolvableKeyT, ValueT, WrappedT: Catalog](
    Catalog[KeyT, ResolvableKeyT, ValueT]
):
    """
    A catalog proxy.
    """

    def __init__(
        self,
        wrapped: Intersection[WrappedT, Catalog[KeyT, ResolvableKeyT, ValueT]],
        /,
    ):
        self.__wrapped__ = wrapped

    @override
    def __len__(self) -> int:
        return len(self.__wrapped__)

    @override
    def __iter__(self) -> Iterator[ValueT]:
        return iter(self.__wrapped__)

    @override
    def __contains__(self, key: Any) -> bool:
        return key in self.__wrapped__

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self.__wrapped__[key]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self.__wrapped__.keys()


class MutableCatalogProxy[
    KeyT,
    ResolvableKeyT,
    ValueT,
    ResolvableValueT,
    WrappedT: MutableCatalog,
](
    CatalogProxy[KeyT, ResolvableKeyT, ValueT, WrappedT],
    MutableCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable catalog proxy.
    """

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        self.__wrapped__.remove(*keys)

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self.__wrapped__[key]

    @override
    def clear(self) -> None:
        self.__wrapped__.clear()

    @override
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        self.__wrapped__.add(*values)
