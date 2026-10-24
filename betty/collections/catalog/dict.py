"""
Catalogs backed by dictionaries.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, final, override

from betty.collection import MutableOrderedValueCollection
from betty.collection.catalog import Catalog, MutableCatalog
from betty.freezer import Frozen
from betty.pipeline import pipe
from betty.typing import empty_frozen_dict

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from betty.collections import KeyResolver, ValueResolver


class _DictCatalog[KeyT, ResolvableKeyT, ValueT](Catalog[KeyT, ResolvableKeyT, ValueT]):
    __slots__ = ("_key_resolver", "_values")

    def __init__(
        self,
        values: Mapping[KeyT, ValueT] = empty_frozen_dict,
        /,
        *,
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
    ):
        self._values = dict(values)
        self.__key_resolver = key_resolver

    @final
    def resolve_key(self, key: KeyT | ResolvableKeyT) -> KeyT:
        return self.__key_resolver(key)

    @override
    def __len__(self) -> int:
        return self._values.__len__()

    @override
    def __iter__(self) -> Iterator[ValueT]:
        yield from self._values.values()

    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self.resolve_key(key)
        return key in self._values

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._values[self.resolve_key(key)]

    @override
    def keys(self) -> Iterable[KeyT]:
        return self._values.keys()


class FrozenDictCatalog[KeyT, ResolvableKeyT, ValueT](
    _DictCatalog[KeyT, ResolvableKeyT, ValueT], Frozen
):
    """
    An immutable catalog backed by a dictionary.
    """


class DictCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _DictCatalog[KeyT, ResolvableKeyT, ValueT],
    MutableCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
    MutableOrderedValueCollection[ValueT, ResolvableValueT],
):
    """
    A mutable catalog backed by a dictionary.
    """

    __slots__ = ("_key", "_value_resolver")

    def __init__(
        self,
        values: Iterable[ValueT | ResolvableValueT] = (),
        /,
        *,
        key: Callable[[ValueT], KeyT],
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value_resolver: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(key_resolver=key_resolver)
        self._key = key
        self.__value_resolver = value_resolver
        self.add(*values)

    @override
    def resolve_value(self, value: ValueT | ResolvableValueT) -> ValueT:
        return self.__value_resolver(value)

    @override
    def add(self, *values: ValueT | ResolvableValueT) -> None:
        for value in map(self.resolve_value, values):
            self._values[self._key(value)] = value

    @override
    def remove(self, *keys: KeyT | ResolvableKeyT) -> None:
        for key in keys:
            del self[key]

    @override
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._values[self.resolve_key(key)]

    @override
    def clear(self) -> None:
        self._values.clear()
