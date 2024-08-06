"""
Provide the Cache API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Self, Generic, TypeAlias, AsyncContextManager, overload, Literal

from typing_extensions import TypeVar


_CacheItemValueT = TypeVar("_CacheItemValueT")
_CacheItemValueCoT = TypeVar("_CacheItemValueCoT", covariant=True)
_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)


class CacheItem(Generic[_CacheItemValueCoT], ABC):
    """
    A cache item.
    """

    @property
    @abstractmethod
    def modified(self) -> int | float:
        """
        Get the time this cache item was last modified, in seconds.
        """
        pass

    @abstractmethod
    async def value(self) -> _CacheItemValueCoT:
        """
        Get this cache item's value.
        """
        pass


CacheItemValueSetter: TypeAlias = Callable[[_CacheItemValueT], Awaitable[None]]


class Cache(Generic[_CacheItemValueContraT], ABC):
    """
    Provide a cache.

    Implementations MUST be thread-safe.

    To test your own subclasses, use :py:class:`betty.test_utils.cache.CacheTestBase`.
    """

    @abstractmethod
    def with_scope(self, scope: str) -> Self:
        """
        Return a new nested cache with the given scope.
        """
        pass

    @abstractmethod
    def get(
        self, cache_item_id: str
    ) -> AsyncContextManager[CacheItem[_CacheItemValueContraT] | None]:
        """
        Get the cache item with the given ID.
        """
        pass

    @abstractmethod
    async def set(
        self,
        cache_item_id: str,
        value: _CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        """
        Add or update a cache item.
        """
        pass

    @overload
    def getset(
        self, cache_item_id: str
    ) -> AsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT],
        ]
    ]:
        pass

    @overload
    def getset(
        self, cache_item_id: str, *, wait: Literal[False] = False
    ) -> AsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        pass

    @abstractmethod
    def getset(
        self, cache_item_id: str, *, wait: bool = True
    ) -> AsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        """
        Get the cache item with the given ID, and provide a setter to add or update it within the same atomic operation.

        If ``wait`` is ``False`` and no lock can be acquired, return ``None, None``.
        Otherwise return:
        0. A cache item if one could be found, or else ``None``.
        1. An asynchronous setter that takes the cache item's value as its only argument.
        """
        pass

    @abstractmethod
    async def delete(self, cache_item_id: str) -> None:
        """
        Delete the cache item with the given ID.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear all items from the cache.
        """
        pass
