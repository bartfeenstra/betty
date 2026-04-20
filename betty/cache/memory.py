"""
Provide caching that stores cache items in volatile memory.
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass
from typing import Self, final, override

from betty.cache import CacheItem
from betty.cache._base import _CommonCacheBase, _CommonCacheBaseState, _StaticCacheItem
from betty.typing import threadsafe

type _MemoryCacheStore[CacheItemValueT] = MutableMapping[
    tuple[str, ...],
    CacheItem[CacheItemValueT] | None | _MemoryCacheStore[CacheItemValueT],
]


@final
@dataclass(frozen=True)
class _MemoryCacheState(_CommonCacheBaseState):
    store: _MemoryCacheStore


@final
@threadsafe
class MemoryCache[CacheItemValueT](_CommonCacheBase[CacheItemValueT]):
    """
    Provide a cache that stores cache items in volatile memory.
    """

    _store: _MemoryCacheStore[CacheItemValueT]

    def __init__(
        self,
        *,
        scopes: Sequence[str] = (),
        state: _MemoryCacheState | None = None,
    ):
        super().__init__(scopes=scopes, state=state)
        if state is None:
            self._store = {}
        else:
            self._store = state.store

    @override
    def with_scope(self, scope: str, /) -> Self:
        return type(self)(
            scopes=(*self._scopes, scope),
            state=_MemoryCacheState(
                self._cache_lock, self._cache_item_lock_ledger, self._store
            ),
        )

    def _cache_item_key(self, cache_item_id: str) -> tuple[str, ...]:
        return *self._scopes, cache_item_id

    @override
    async def get(self, cache_item_id: str, /) -> CacheItem[CacheItemValueT] | None:
        cache_item = self._store.get(self._cache_item_key(cache_item_id), None)
        if isinstance(cache_item, CacheItem):
            return cache_item  # ty:ignore[invalid-return-type]
        return None

    @override
    async def set(
        self,
        cache_item_id: str,
        value: CacheItemValueT,
        *,
        modified: float | None = None,
    ) -> None:
        self._store[self._cache_item_key(cache_item_id)] = _StaticCacheItem(
            value, modified
        )

    @override
    async def delete(self, cache_item_id: str, /) -> None:
        self._store.pop(self._cache_item_key(cache_item_id), None)

    @override
    async def clear(self) -> None:
        self._store.clear()
