"""
Provide the Cache API.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Self, Generic, TypeAlias, AsyncContextManager, overload, Literal

import typing_extensions
from typing_extensions import TypeVar

if typing_extensions.TYPE_CHECKING:
    from pathlib import Path


_CacheItemValueT = TypeVar("_CacheItemValueT")
_CacheItemValueCoT = TypeVar("_CacheItemValueCoT", covariant=True)
_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)


class CacheItem(Generic[_CacheItemValueCoT]):
    """
    A cache item.
    """

    @property
    def modified(self) -> int | float:
        """
        Get the time this cache item was last modified, in seconds.
        """
        raise NotImplementedError

    async def value(self) -> _CacheItemValueCoT:
        """
        Get this cache item's value.
        """
        raise NotImplementedError


CacheItemValueSetter: TypeAlias = Callable[[_CacheItemValueT], Awaitable[None]]


class Cache(Generic[_CacheItemValueContraT]):
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
    ) -> AsyncContextManager[CacheItem[_CacheItemValueContraT] | None]:
        """
        Get the cache item with the given ID.
        """
        raise NotImplementedError

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
        raise NotImplementedError

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
class FileCache:  # noqa D101
    @property
    def path(self) -> Path:  # type: ignore[empty-body]  # noqa D102
        pass

    async def clear(self) -> None:  # noqa D102
        pass
