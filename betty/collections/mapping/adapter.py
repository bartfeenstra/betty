"""
Adapters between Betty and Python mappings.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, MutableMapping, Sequence
from contextlib import suppress
from itertools import chain
from typing import Any, overload, override

from ty_extensions import Intersection
from typing_extensions import sentinel

from betty.collection.mapping import BettyMapping, MutableBettyMapping


class MappingAdapter[KeyT, ResolvableKeyT, ValueT, WrappedT: Mapping](
    BettyMapping[KeyT, ResolvableKeyT, ValueT]
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    def __init__(self, wrapped: Intersection[WrappedT, Mapping[KeyT, ValueT]], /):
        self.__wrapped__ = wrapped

    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self.__wrapped__[self.resolve_key(key)]

    @overload
    def get[T](self, key: KeyT | ResolvableKeyT, default: T, /) -> ValueT | T:
        pass

    @overload
    def get(self, key: KeyT | ResolvableKeyT, /) -> ValueT:
        pass

    @override
    def get(self, key, *args):
        return self.__wrapped__.get(self.resolve_key(key), *args)

    @override
    def __iter__(self) -> Iterator[KeyT]:
        return iter(self.__wrapped__)

    @override
    def __len__(self) -> int:
        return len(self.__wrapped__)

    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self.resolve_key(key)
        return key in self.__wrapped__


_NoMutableMappingAdapterDefault = sentinel("_NoMutableMappingAdapterDefault")


class MutableMappingAdapter[
    KeyT,
    ResolvableKeyT,
    ValueT,
    ResolvableValueT,
    WrappedT: MutableMapping,
](
    MappingAdapter[
        KeyT,
        ResolvableKeyT,
        ValueT,
        Intersection[WrappedT, MutableMapping[KeyT, ValueT]],
    ],
    MutableBettyMapping[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    def __setitem__(
        self, key: KeyT | ResolvableKeyT, value: ValueT | ResolvableValueT
    ) -> None:
        self.__wrapped__[self.resolve_key(key)] = self.resolve_value(value)

    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self.__wrapped__[self.resolve_key(key)]

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
        self.__wrapped__.update({
            self.resolve_key(key): self.resolve_value(value)  # ty:ignore[invalid-argument-type]
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
    def setdefault(self, key, default=_NoMutableMappingAdapterDefault):
        return self.__wrapped__.setdefault(
            self.resolve_key(key),
            None
            if default is _NoMutableMappingAdapterDefault
            else self.resolve_value(default),
        )

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
    def pop(self, key, default=_NoMutableMappingAdapterDefault):
        key = self.resolve_key(key)
        if default is _NoMutableMappingAdapterDefault:
            return self.__wrapped__.pop(key)
        return self.__wrapped__.pop(key, default)

    @override
    def popitem(self) -> tuple[KeyT, ValueT]:
        return self.__wrapped__.popitem()

    @override
    def clear(self) -> None:
        self.__wrapped__.clear()
