"""
Provide the Cache API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Self

from betty.typing import threadsafe

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager


class CacheItem[CacheItemValueT](ABC):
    """
    A cache item.
    """

    @property
    @abstractmethod
    def modified(self) -> int | float:
        """
        Get the time this cache item was last modified, in seconds.
        """

    @abstractmethod
    async def value(self) -> CacheItemValueT:
        """
        Get this cache item's value.
        """


type CacheItemValueSetter[_CacheItemValueT] = Callable[
    [_CacheItemValueT], Awaitable[None]
]


@threadsafe
class Cache[CacheItemValueT](ABC):
    """
    A cache.

    To test your own subclasses, use :py:class:`betty.test_utils.cache.CacheTestBase`.
    """

    @abstractmethod
    def with_scope(self, scope: str, /) -> Self:
        """
        Return a new nested cache with the given scope.
        """

    async def has(self, cache_item_id: str, /) -> bool:
        """
        Check if a cache item with the given ID exists.
        """
        return await self.get(cache_item_id) is not None

    @abstractmethod
    def hasset(
        self, cache_item_id: str, /
    ) -> AbstractAsyncContextManager[CacheItemValueSetter[CacheItemValueT] | None]:
        """
        Check if a cache item with the given ID exists, and if not, provide a setter to add or update it within the same atomic operation.
        """

    @abstractmethod
    async def get(self, cache_item_id: str, /) -> CacheItem[CacheItemValueT] | None:
        """
        Get the cache item with the given ID.
        """

    @abstractmethod
    async def set(
        self,
        cache_item_id: str,
        value: CacheItemValueT,
        *,
        modified: float | None = None,
    ) -> None:
        """
        Add or update a cache item.
        """

    @abstractmethod
    def getset(
        self, cache_item_id: str, /
    ) -> AbstractAsyncContextManager[
        CacheItemValueSetter[CacheItemValueT] | CacheItem[CacheItemValueT]
    ]:
        """
        Get the cache item with the given ID, or provide a setter to add it within the same atomic operation.
        """

    @abstractmethod
    async def delete(self, cache_item_id: str, /) -> None:
        """
        Delete the cache item with the given ID.

        This operation s unsafe and MAY cause other concurrent operations on this cache to fail.
        """

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear all items from the cache.

        This operation s unsafe and MAY cause other concurrent operations on this cache to fail.
        """
