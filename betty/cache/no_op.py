"""
Provide no-op caching.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.cache import Cache, CacheItem, CacheItemValueSetter
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@final
@threadsafe
class NoOpCache(Cache[Any]):
    """
    Provide a cache that does nothing.
    """

    @override
    def with_scope(self, scope: str, /) -> Self:
        return self

    async def _setter(self, value: Any) -> None:
        pass

    @override
    async def has(self, cache_item_id: str, /) -> bool:
        return False

    @override
    @asynccontextmanager
    async def hasset(
        self, cache_item_id: str, /
    ) -> AsyncIterator[CacheItemValueSetter[Any] | None]:
        yield self._setter
        return

    @override
    async def get(self, cache_item_id: str, /) -> CacheItem[Any] | None:
        return None

    @override
    async def set(
        self,
        cache_item_id: str,
        value: Any,
        *,
        modified: int | float | None = None,
    ) -> None:
        return

    @override
    @asynccontextmanager
    async def getset(
        self, cache_item_id: str, /
    ) -> AsyncIterator[CacheItemValueSetter[Any] | CacheItem[Any]]:
        yield self._setter
        return

    @override
    async def delete(self, cache_item_id: str, /) -> None:
        return

    @override
    async def clear(self) -> None:
        return
