"""
Catalogs backed by mappings.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, final, override

from betty.collection.catalog import Catalog, MutableCatalog
from betty.collections import KeyResolvable, ValueResolvable
from betty.freezers.attr import AttrFreezable
from betty.pipeline import pipe

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping

    from ty_extensions import Intersection

    from betty.collections import KeyResolver, ValueResolver


class MappingCatalog[KeyT, ResolvableKeyT, ValueT, WrappedT: Mapping](
    KeyResolvable[KeyT, ResolvableKeyT], Catalog[KeyT, ResolvableKeyT, ValueT]
):
    """
    An immutable catalog backed by a mapping.
    """

    __slots__ = ("__key", "__wrapped__")

    def __init__(
        self,
        wrapped: Intersection[WrappedT, Mapping[KeyT, ValueT]],
        /,
        *,
        key: KeyResolver[KeyT, ResolvableKeyT] = pipe,
    ):
        self.__key = key
        self.__wrapped__ = wrapped

    @final
    @override
    def resolve_key(self, key: KeyT | ResolvableKeyT, /) -> KeyT:
        return self.__key(key)

    @override
    def __len__(self) -> int:
        return self.__wrapped__.__len__()

    @override
    def __iter__(self) -> Iterator[ValueT]:
        yield from self.__wrapped__.values()

    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self.resolve_key(key)
        return key in self.__wrapped__

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self.__wrapped__[self.resolve_key(key)]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self.__wrapped__.keys()


class MutableMappingCatalog[
    KeyT,
    ResolvableKeyT,
    ValueT,
    ResolvableValueT,
    WrappedT: MutableMapping,
](
    AttrFreezable,
    ValueResolvable[ValueT, ResolvableValueT],
    MappingCatalog[KeyT, ResolvableKeyT, ValueT, WrappedT],
    MutableCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable catalog backed by a mapping.
    """

    def __init__(
        self,
        wrapped: Intersection[WrappedT, MutableMapping[KeyT, ValueT]],
        keyer: Callable[[ValueT], KeyT | ResolvableKeyT],
        /,
        *,
        key: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        self.__value = value
        super().__init__(wrapped, key=key)
        self._keyer = keyer

    @final
    @override
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        return self.__value(value)

    @override
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        self.assert_not_frozen()
        for value in map(self.resolve_value, values):
            self.__wrapped__[self.resolve_key(self._keyer(value))] = value

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        self.assert_not_frozen()
        for key in keys:
            del self[key]

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        self.assert_not_frozen()
        del self.__wrapped__[self.resolve_key(key)]

    @override
    def clear(self) -> None:
        self.assert_not_frozen()
        self.__wrapped__.clear()
