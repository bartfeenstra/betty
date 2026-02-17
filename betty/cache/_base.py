from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial
from typing import Any, Self, override

from betty.cache import Cache, CacheItem, CacheItemValueSetter
from betty.concurrent import AsynchronizedLock, Ledger
from betty.typing import threadsafe


class _StaticCacheItem[CacheItemValueT](CacheItem[CacheItemValueT]):
    __slots__ = "_value", "_modified"

    def __init__(
        self,
        value: CacheItemValueT,
        modified: int | float | None = None,
    ):
        self._value = value
        self._modified = datetime.now().timestamp() if modified is None else modified

    @override
    async def value(self) -> CacheItemValueT:
        return self._value

    @override
    @property
    def modified(self) -> int | float:
        return self._modified


class _CommonCacheBaseState[CacheT: Cache[Any]]:
    def __init__(
        self,
        cache_lock: AsynchronizedLock,
        cache_item_lock_ledger: Ledger,
    ):
        self.cache_lock = cache_lock
        self.cache_item_lock_ledger = cache_item_lock_ledger


@threadsafe
class _CommonCacheBase[CacheItemValueT](Cache[CacheItemValueT]):
    def __init__(
        self,
        *,
        scopes: Sequence[str] | None = None,
        state: _CommonCacheBaseState[Self] | None = None,
    ):
        self._scopes = scopes or ()
        if state is not None:
            self._cache_lock = state.cache_lock
            self._cache_item_lock_ledger = state.cache_item_lock_ledger
        else:
            self._cache_lock = AsynchronizedLock.new_threadsafe()
            self._cache_item_lock_ledger = Ledger(self._cache_lock)

    @override
    @asynccontextmanager
    async def hasset(
        self, cache_item_id: str, /
    ) -> AsyncIterator[CacheItemValueSetter[CacheItemValueT] | None]:
        if await self.has(cache_item_id):
            yield None
            return
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
            if await self.has(cache_item_id):
                yield None
            yield partial(self.set, cache_item_id)
        return

    @override
    @asynccontextmanager
    async def getset(
        self, cache_item_id: str, /
    ) -> AsyncIterator[
        CacheItemValueSetter[CacheItemValueT] | CacheItem[CacheItemValueT]
    ]:
        if cache_item := await self.get(cache_item_id):
            yield cache_item
            return
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
            if cache_item := await self.get(cache_item_id):
                yield cache_item
                return
            yield partial(self.set, cache_item_id)
        return
