"""
Provide the Cache API.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Self, Generic, TypeAlias, AsyncContextManager, overload, Literal

import typing_extensions
from typing_extensions import TypeVar

CacheItemValueT = TypeVar("CacheItemValueT")
CacheItemValueCoT = TypeVar("CacheItemValueCoT", covariant=True)
CacheItemValueContraT = TypeVar("CacheItemValueContraT", contravariant=True)


class CacheItem(Generic[CacheItemValueCoT]):
    @property
    def modified(self) -> int | float:
        """
        Get the time this cache item was last modified, in seconds.
        """
        raise NotImplementedError

    async def value(self) -> CacheItemValueCoT:
        """
        Get this cache item's value.
        """
        raise NotImplementedError


CacheItemValueSetter: TypeAlias = Callable[[CacheItemValueT], Awaitable[None]]


class Cache(Generic[CacheItemValueContraT]):
    """
    Provide a cache.

    Implementations MUST be thread-safe.
    """

    def with_scope(self, scope: str) -> Self:
        """
        Return a new nested cache with the given scope.
        """
        raise NotImplementedError

    def get(
        self, cache_item_id: str
    ) -> AsyncContextManager[CacheItem[CacheItemValueContraT] | None]:
        """
        Get the cache item with the given ID.
        """
        raise NotImplementedError

    async def set(
        self,
        cache_item_id: str,
        value: CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        """
        Add or update a cache item.
        """
        raise NotImplementedError

    @overload
    def getset(self, cache_item_id: str) -> AsyncContextManager[
        tuple[
            CacheItem[CacheItemValueContraT] | None,
            CacheItemValueSetter[CacheItemValueContraT],
        ]
    ]:
        pass

    @overload
    def getset(
        self, cache_item_id: str, *, wait: Literal[False] = False
    ) -> AsyncContextManager[
        tuple[
            CacheItem[CacheItemValueContraT] | None,
            CacheItemValueSetter[CacheItemValueContraT] | None,
        ]
    ]:
        pass

    def getset(self, cache_item_id: str, *, wait: bool = True) -> AsyncContextManager[
        tuple[
            CacheItem[CacheItemValueContraT] | None,
            CacheItemValueSetter[CacheItemValueContraT] | None,
        ]
    ]:
        """
        Get the cache item with the given ID, and provide a setter to add or update it within the same atomic operation.

        If ``wait`` is ``False`` and no lock can be acquired, return ``None, None``.
        Otherwise return:
        0. A cache item if one could be found, or else ``None``.
        1. An asynchronous setter that takes the cache item's value as its only argument.
        """
        raise NotImplementedError

    async def delete(self, cache_item_id: str) -> None:
        """
        Delete the cache item with the given ID.
        """
        raise NotImplementedError

    async def clear(self) -> None:
        """
        Clear all items from the cache.
        """
        raise NotImplementedError


@typing_extensions.deprecated(
    f"This class is deprecated as of Betty 0.3.3, and will be removed in Betty 0.4.x. It exists only for App.cache's backwards compatibility. Use {Cache} instead."
)
class FileCache:
    @property
    def path(self) -> Path:  # type: ignore[empty-body]
        pass

    async def clear(self) -> None:
        pass
