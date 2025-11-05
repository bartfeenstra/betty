from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial
from typing import Any, Generic, Self, TypeVar

from typing_extensions import override

from betty.cache import Cache, CacheItem, CacheItemValueSetter
from betty.concurrent import AsynchronizedLock, Ledger
from betty.typing import threadsafe

_T = TypeVar("_T")
_CacheT = TypeVar("_CacheT", bound=Cache[Any])
_CacheItemValueCoT = TypeVar("_CacheItemValueCoT", covariant=True)
_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)


class _StaticCacheItem(CacheItem[_CacheItemValueCoT], Generic[_CacheItemValueCoT]):
    __slots__ = "_value", "_modified"

    def __init__(
        self,
        value: _CacheItemValueCoT,
        modified: int | float | None = None,
    ):
        self._value = value
        self._modified = datetime.now().timestamp() if modified is None else modified

    @override
    async def value(self) -> _CacheItemValueCoT:
        return self._value

    @override
    @property
    def modified(self) -> int | float:
        return self._modified


class _CommonCacheBaseState(Generic[_CacheT]):
    def __init__(
        self,
        cache_lock: AsynchronizedLock,
        cache_item_lock_ledger: Ledger,
    ):
        self.cache_lock = cache_lock
        self.cache_item_lock_ledger = cache_item_lock_ledger


@threadsafe
class _CommonCacheBase(Cache[_CacheItemValueContraT], Generic[_CacheItemValueContraT]):
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
    ) -> AsyncIterator[CacheItemValueSetter[_CacheItemValueContraT] | None]:
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
        CacheItemValueSetter[_CacheItemValueContraT] | CacheItem[_CacheItemValueContraT]
    ]:
        if cache_item := await self.get(cache_item_id):
            yield cache_item
            return
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
            if cache_item := await self.get(cache_item_id):
                yield cache_item
            yield partial(self.set, cache_item_id)
        return
