"""
Adapters between Betty and Python mappings.
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from contextlib import suppress
from itertools import chain
from typing import TYPE_CHECKING, Any, overload, override

from typing_extensions import sentinel

from betty.collection.mapping import MutableResolvedMapping, ResolvedMapping
from betty.pipeline import pipe

if TYPE_CHECKING:
    from betty.collections import KeyResolver, ValueResolver


class ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT](
    ResolvedMapping[KeyT, ResolvableKeyT, ValueT]
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    def __init__(
        self,
        values: Mapping[KeyT, ValueT],
        /,
        *,
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
    ):
        self._values = values
        self._key_resolver = key_resolver

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._values[self._key_resolver(key)]

    @overload
    def get[T](self, key: KeyT | ResolvableKeyT, default: T, /) -> ValueT | T:
        pass

    @overload
    def get(self, key: KeyT | ResolvableKeyT, /) -> ValueT:
        pass

    @override
    def get(self, key, *args):
        return self._values.get(self._key_resolver(key), *args)

    @override
    def __iter__(self) -> Iterator[KeyT]:
        return iter(self._values)

    @override
    def __len__(self) -> int:
        return len(self._values)

    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self._key_resolver(key)
        return key in self._values


_NoMutableResolvedMappingAdapterDefault = sentinel(
    "_NoMutableResolvedMappingAdapterDefault"
)


class MutableResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT],
    MutableResolvedMapping[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    _values: MutableMapping[KeyT, ValueT]

    def __init__(
        self,
        values: MutableMapping[KeyT, ValueT],
        /,
        *,
        key_resolver: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value_resolver: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(values, key_resolver=key_resolver)
        self._value_resolver = value_resolver

    def __setitem__(
        self, key: KeyT | ResolvableKeyT, value: ValueT | ResolvableValueT
    ) -> None:
        self._values[self._key_resolver(key)] = self._value_resolver(value)

    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._values[self._key_resolver(key)]

    @overload
    def update(
        self,
        other: Mapping[KeyT | ResolvableKeyT, ValueT | ResolvableValueT]
        | Iterable[tuple[KeyT | ResolvableKeyT, ValueT | ResolvableValueT]],
        /,
        **kwargs: ValueT | ResolvableValueT,
    ) -> None:
        pass

    @overload
    def update(self, **kwargs: ValueT | ResolvableValueT) -> None:
        pass

    @override
    def update(self, other=None, **kwargs) -> None:
        items: Iterable[tuple[str, ValueT | ResolvableValueT]] = kwargs.items()
        if isinstance(other, Mapping):
            items = chain(items, other.items())
        elif isinstance(other, Sequence):
            items = chain(items, other)
        self._values.update({
            self._key_resolver(key): self._value_resolver(value)  # ty:ignore[invalid-argument-type]
            for key, value in items
        })

    @overload
    def setdefault[T](
        self: MutableMapping[KeyT, T | None],
        key: KeyT | ResolvableKeyT,
        default: None = None,
        /,
    ) -> T | None:
        pass

    @overload
    def setdefault(
        self, key: KeyT | ResolvableKeyT, default: ValueT | ResolvableValueT, /
    ) -> ValueT:
        pass

    @override
    def setdefault(self, key, default=_NoMutableResolvedMappingAdapterDefault):
        return self._values.setdefault(
            self._key_resolver(key),
            None
            if default is _NoMutableResolvedMappingAdapterDefault
            else self._value_resolver(default),
        )  # ty:ignore[no-matching-overload]

    @overload
    def pop(self, key: KeyT | ResolvableKeyT, /) -> ValueT:
        pass

    @overload
    def pop(
        self, key: KeyT | ResolvableKeyT, /, default: ValueT | ResolvableValueT
    ) -> ValueT:
        pass

    @overload
    def pop[T](self, key: KeyT | ResolvableKeyT, /, default: T) -> ValueT | T:
        pass

    @override
    def pop(self, key, default=_NoMutableResolvedMappingAdapterDefault):
        key = self._key_resolver(key)
        if default is _NoMutableResolvedMappingAdapterDefault:
            return self._values.pop(key)
        return self._values.pop(key, default)

    @override
    def popitem(self) -> tuple[KeyT, ValueT]:
        return self._values.popitem()
