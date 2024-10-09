"""
Provide caching that stores cache items in volatile memory.
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import TypeAlias, Generic, Self, cast, TypeVar, final

from typing_extensions import override

from betty.cache import CacheItem
from betty.cache._base import _CommonCacheBase, _StaticCacheItem
from betty.typing import threadsafe

_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)

_MemoryCacheStore: TypeAlias = MutableMapping[
    str,
    "CacheItem[_CacheItemValueContraT] | None | _MemoryCacheStore[_CacheItemValueContraT]",
]


@final
@threadsafe
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
        _store: _MemoryCacheStore[_CacheItemValueContraT] | None = None,
    ):
        super().__init__(scopes=scopes)
        self._store: _MemoryCacheStore[_CacheItemValueContraT] = _store or {}

    @override
    def _with_scope(self, scope: str) -> Self:
        return type(self)(
            scopes=(*self._scopes, scope),
            _store=cast(
                "_MemoryCacheStore[_CacheItemValueContraT]",
                self._store.setdefault(scope, {}),
            ),
        )

    @override
    async def _get(
        self, cache_item_id: str
    ) -> CacheItem[_CacheItemValueContraT] | None:
        cache_item = self._store.get(cache_item_id, None)
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
        self._store[cache_item_id] = _StaticCacheItem(value, modified)

    @override
    async def _delete(self, cache_item_id: str) -> None:
        self._store.pop(cache_item_id, None)

    @override
    async def _clear(self) -> None:
        self._store.clear()
