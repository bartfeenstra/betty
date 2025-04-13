"""
Provide caching that stores cache items in volatile memory.
"""

from __future__ import annotations

import multiprocessing
from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING, Generic, Self, TypeAlias, TypeVar, final

from typing_extensions import override

from betty.cache import CacheItem
from betty.cache._base import _CommonCacheBase, _CommonCacheBaseState, _StaticCacheItem
from betty.typing import processsafe

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager

    from betty.concurrent import AsynchronizedLock, Ledger

_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)

_MemoryCacheStore: TypeAlias = MutableMapping[
    tuple[str, ...],
    "CacheItem[_CacheItemValueContraT] | None | _MemoryCacheStore[_CacheItemValueContraT]",
]


@final
class _MemoryCacheState(
    Generic[_CacheItemValueContraT],
    _CommonCacheBaseState["MemoryCache[_CacheItemValueContraT]"],
):
    def __init__(
        self,
        cache_lock: AsynchronizedLock,
        cache_item_lock_ledger: Ledger,
        store: _MemoryCacheStore[_CacheItemValueContraT],
    ):
        super().__init__(cache_lock, cache_item_lock_ledger)
        self.store = store


@final
@processsafe
class MemoryCache(
    _CommonCacheBase[_CacheItemValueContraT], Generic[_CacheItemValueContraT]
):
    """
    Provide a cache that stores cache items in volatile memory.
    """

    def __init__(
        self,
        *,
        scopes: Sequence[str] | None = None,
        manager: SyncManager | _MemoryCacheState[_CacheItemValueContraT] | None = None,
    ):
        super().__init__(scopes=scopes, manager=manager)
        if isinstance(manager, _MemoryCacheState):
            self._store = manager.store
        else:
            self._store = multiprocessing.Manager().dict()

    @override
    def with_scope(self, scope: str) -> Self:
        return type(self)(
            scopes=(*self._scopes, scope),
            manager=_MemoryCacheState[_CacheItemValueContraT](
                self._cache_lock, self._cache_item_lock_ledger, self._store
            ),
        )

    def _cache_item_key(self, cache_item_id: str) -> tuple[str, ...]:
        return *self._scopes, cache_item_id

    @override
    async def _get(
        self, cache_item_id: str
    ) -> CacheItem[_CacheItemValueContraT] | None:
        cache_item = self._store.get(self._cache_item_key(cache_item_id), None)
        if isinstance(cache_item, CacheItem):
            return cache_item
        return None

    @override
    async def _set(
        self,
        cache_item_id: str,
        value: _CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        self._store[self._cache_item_key(cache_item_id)] = _StaticCacheItem(
            value, modified
        )

    @override
    async def _delete(self, cache_item_id: str) -> None:
        self._store.pop(self._cache_item_key(cache_item_id), None)

    @override
    async def _clear(self) -> None:
        self._store.clear()
