"""
Adapters between Betty and Python mappings.
"""

from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from contextlib import suppress
from itertools import chain
from typing import Any, final, overload, override

from betty.collection.mapping import MutableResolvedMapping, ResolvedMapping
from betty.functools import passthrough
from betty.typing import Void


class _ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT](
    ResolvedMapping[KeyT, ResolvableKeyT, ValueT]
):
    def __init__(
        self,
        upstream: Mapping[KeyT, ValueT],
        *,
        key_resolver: Callable[[KeyT | ResolvableKeyT], KeyT] = passthrough,
    ):
        self._upstream = upstream
        self._key_resolver = key_resolver

    @final
    @override
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        return self._upstream[self._key_resolver(key)]

    @overload
    def get[T](self, key: KeyT | ResolvableKeyT, default: T, /) -> ValueT | T:
        pass

    @overload
    def get(self, key: KeyT | ResolvableKeyT, default: None = None, /) -> ValueT | None:
        pass

    @final
    @override
    def get(self, key, default=None):
        return self._upstream.get(self._key_resolver(key), default)

    @final
    @override
    def __iter__(self) -> Iterator[KeyT]:
        return iter(self._upstream)

    @final
    @override
    def __len__(self) -> int:
        return len(self._upstream)

    @final
    @override
    def __contains__(self, key: Any) -> bool:
        with suppress(Exception):
            key = self._key_resolver(key)
        return key in self._upstream


@final
class ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT](
    _ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT]
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """


@final
class MutableResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    _ResolvedMappingAdapter[KeyT, ResolvableKeyT, ValueT],
    MutableResolvedMapping[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    Decorate another mapping to resolve any values before proxying them.
    """

    _upstream: MutableMapping[KeyT, ValueT]

    def __init__(
        self,
        upstream: MutableMapping[KeyT, ValueT],
        *,
        key_resolver: Callable[[KeyT | ResolvableKeyT], KeyT] = passthrough,
        value_resolver: Callable[[ValueT | ResolvableValueT], ValueT] = passthrough,
    ):
        super().__init__(upstream, key_resolver=key_resolver)
        self._value_resolver = value_resolver

    def __setitem__(
        self, key: KeyT | ResolvableKeyT, value: ValueT | ResolvableValueT
    ) -> None:
        self._upstream[self._key_resolver(key)] = self._value_resolver(value)

    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        del self._upstream[self._key_resolver(key)]

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
            items = chain(items, other.items())  # ty:ignore[invalid-assignment]
        elif isinstance(other, Sequence):
            items = chain(items, other)  # ty:ignore[invalid-assignment]
        self._upstream.update(
            {
                self._key_resolver(key): self._value_resolver(value)  # ty:ignore[invalid-argument-type]
                for key, value in items
            }
        )

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
    def setdefault(self, key, default=Void):
        return self._upstream.setdefault(
            self._key_resolver(key),
            None if default is Void else self._value_resolver(default),
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
    def pop(self, key, default=Void):
        key = self._key_resolver(key)
        if default is Void:
            return self._upstream.pop(key)
        return self._upstream.pop(key, default)

    @override
    def popitem(self) -> tuple[KeyT, ValueT]:
        return self._upstream.popitem()
