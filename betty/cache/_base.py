from abc import abstractmethod
from asyncio import sleep
from collections import defaultdict
from collections.abc import Sequence, MutableMapping, AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Generic, Self, overload, AsyncContextManager, Literal, TypeVar

from typing_extensions import override

from betty.cache import (
    Cache,
    CacheItem,
    CacheItemValueSetter,
)
from betty.concurrent import AsynchronizedLock, Lock

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


class _CacheItemLock(Lock):
    def __init__(
        self,
        cache_item_id: str,
        wait: bool,
        cache_lock: Lock,
        cache_items_locked: MutableMapping[str, bool],
    ):
        self._cache_item_id = cache_item_id
        self._wait = wait
        self._cache_lock = cache_lock
        self._cache_items_locked = cache_items_locked

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        if wait:
            while True:
                async with self._cache_lock:
                    if self._can_acquire():
                        return self._acquire()
                await sleep(0)
        else:
            async with self._cache_lock:
                if self._can_acquire():
                    return self._acquire()
                return False

    def _can_acquire(self) -> bool:
        return not self._cache_items_locked[self._cache_item_id]

    def _acquire(self) -> bool:
        self._cache_items_locked[self._cache_item_id] = True
        return True

    @override
    async def release(self) -> None:
        self._cache_items_locked[self._cache_item_id] = False


class _CommonCacheBase(Cache[_CacheItemValueContraT], Generic[_CacheItemValueContraT]):
    def __init__(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ):
        self._scopes = scopes or ()
        self._scoped_caches: MutableMapping[str, Self] = {}
        self._cache_lock = AsynchronizedLock.threading()
        self.__cache_items_locked: MutableMapping[str, bool] = defaultdict(
            lambda: False
        )

    def _cache_item_lock(self, cache_item_id: str, *, wait: bool = True) -> Lock:
        return _CacheItemLock(
            cache_item_id, wait, self._cache_lock, self.__cache_items_locked
        )

    @override
    def with_scope(self, scope: str) -> Self:
        try:
            return self._scoped_caches[scope]
        except KeyError:
            self._scoped_caches[scope] = self._with_scope(scope)
            return self._scoped_caches[scope]

    @abstractmethod
    def _with_scope(self, scope: str) -> Self:
        pass

    @override
    @asynccontextmanager
    async def get(
        self, cache_item_id: str
    ) -> AsyncIterator[CacheItem[_CacheItemValueContraT] | None]:
        async with self._cache_item_lock(cache_item_id):
            yield await self._get(cache_item_id)

    @abstractmethod
    async def _get(
        self, cache_item_id: str
    ) -> CacheItem[_CacheItemValueContraT] | None:
        pass

    @override
    async def set(
        self,
        cache_item_id: str,
        value: _CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        async with self._cache_item_lock(cache_item_id):
            await self._set(cache_item_id, value, modified=modified)

    @abstractmethod
    async def _set(
        self,
        cache_item_id: str,
        value: _CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        pass

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

    @asynccontextmanager  # type: ignore[misc]
    async def getset(
        self, cache_item_id: str, *, wait: bool = True
    ) -> AsyncIterator[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        lock = self._cache_item_lock(cache_item_id)
        if await lock.acquire(wait=wait):
            try:

                async def _setter(value: _CacheItemValueContraT) -> None:
                    await self._set(cache_item_id, value)

                yield await self._get(cache_item_id), _setter
                return
            finally:
                await lock.release()
        yield None, None

    @override
    async def delete(self, cache_item_id: str) -> None:
        async with self._cache_item_lock(cache_item_id):
            await self._delete(cache_item_id)

    @abstractmethod
    async def _delete(self, cache_item_id: str) -> None:
        pass

    @override
    async def clear(self) -> None:
        async with self._cache_lock:
            await self._clear()

    @abstractmethod
    async def _clear(self) -> None:
        pass
