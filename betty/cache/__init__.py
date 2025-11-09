"""
Provide the Cache API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Generic, Self, TypeAlias

from typing_extensions import TypeVar

from betty.typing import threadsafe

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

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

    @abstractmethod
    async def value(self) -> _CacheItemValueCoT:
        """
        Get this cache item's value.
        """


CacheItemValueSetter: TypeAlias = Callable[[_CacheItemValueT], Awaitable[None]]


@threadsafe
class Cache(Generic[_CacheItemValueContraT], ABC):
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
    ) -> AbstractAsyncContextManager[
        CacheItemValueSetter[_CacheItemValueContraT] | None
    ]:
        """
        Check if a cache item with the given ID exists, and if not, provide a setter to add or update it within the same atomic operation.
        """

    @abstractmethod
    async def get(
        self, cache_item_id: str, /
    ) -> CacheItem[_CacheItemValueContraT] | None:
        """
        Get the cache item with the given ID.
        """

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

    @abstractmethod
    def getset(
        self, cache_item_id: str, /
    ) -> AbstractAsyncContextManager[
        CacheItemValueSetter[_CacheItemValueContraT] | CacheItem[_CacheItemValueContraT]
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
