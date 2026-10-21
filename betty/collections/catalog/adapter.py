"""
Adapters between catalogs and Python data types.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, override

from betty.collection.catalog import Catalog, MutableCatalog
from betty.pipeline import pipe
from betty.typing import empty_frozen_dict

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from betty.collections import KeyResolver, ValueResolver


# @todo We have no Python types to map to for catalogs.
# @todo We should probably move (most of) these classes into DictCatalog.
# @todo
class CatalogAdapter[KeyT, ResolvableKeyT, ValueT](
    Catalog[KeyT, ResolvableKeyT, ValueT]
):
    """
    A collection of values that are accessible by their primary keys.
    """

    def __init__(
        self,
        values: Mapping[KeyT, ValueT]
        | Iterable[tuple[KeyT, ValueT]] = empty_frozen_dict,
        /,
        *,
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
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


class MutableCatalogAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    CatalogAdapter[KeyT, ResolvableKeyT, ValueT],
    MutableCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable ordered collection of values that are accessible by their primary keys.
    """

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
        for value in map(self._value_resolver, values):
            self._values[self._key(value)] = value
