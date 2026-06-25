"""
Mapping types and implementations.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Mapping, MutableMapping
from typing import overload, override

from betty.collection import MutableCollection


class ResolvedMapping[KeyT, ResolvableKeyT, ValueT](Mapping[KeyT, ValueT]):
    """
    A mutable mapping of resolvable keys.
    """

    @override
    @abstractmethod
    def __getitem__(self, key: KeyT | ResolvableKeyT) -> ValueT:
        pass

    @overload
    def get[T](self, key: KeyT | ResolvableKeyT, default: T, /) -> ValueT | T:
        pass

    @overload
    def get(self, key: KeyT | ResolvableKeyT, default: None = None, /) -> ValueT | None:
        pass

    @override
    @abstractmethod
    def get[T](
        self, key: KeyT | ResolvableKeyT, default: T | None = None, /
    ) -> ValueT | None:
        pass


class MutableResolvedMapping[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableMapping[KeyT, ValueT],
    MutableCollection[KeyT],
    ResolvedMapping[KeyT, ResolvableKeyT, ValueT],
):
    """
    A mutable mapping of resolvable keys and values.
    """

    @abstractmethod
    def __setitem__(
        self, key: KeyT | ResolvableKeyT, value: ValueT | ResolvableValueT
    ) -> None:
        pass

    @abstractmethod
    def __delitem__(self, key: KeyT | ResolvableKeyT) -> None:
        pass

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
    @abstractmethod
    def update(self, other=None, **kwargs) -> None:  # ty:ignore[invalid-method-override]
        """
        Update the mapping with the provided values.

        See :py:meth:`collections.abc.MutableMapping.update`.
        """

    @overload
    def setdefault[T](
        self: MutableMapping[KeyT, T | None],
        key: KeyT | ResolvableKeyT,
        default: None = None,
        /,
    ) -> T | None:
        pass

    @overload
    def setdefault[T](
        self, key: KeyT | ResolvableKeyT, default: ValueT | ResolvableValueT, /
    ) -> ValueT:
        pass

    @override
    @abstractmethod
    def setdefault(self, key, default):
        pass

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
    @abstractmethod
    def pop(self, key, default):
        pass

    @override
    @abstractmethod
    def popitem(self) -> tuple[KeyT, ValueT]:
        pass
