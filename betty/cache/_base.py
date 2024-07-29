from abc import abstractmethod
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
from betty.concurrent import _Lock, AsynchronizedLock, MultiLock

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


class _CommonCacheBase(Cache[_CacheItemValueContraT], Generic[_CacheItemValueContraT]):
    def __init__(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ):
        self._scopes = scopes or ()
        self._scoped_caches: dict[str, Self] = {}
        self._locks: MutableMapping[str, _Lock] = defaultdict(
            AsynchronizedLock.threading
        )
        self._locks_lock = AsynchronizedLock.threading()

    async def _lock(self, cache_item_id: str) -> _Lock:
        async with self._locks_lock:
            return self._locks[cache_item_id]

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
        async with await self._lock(cache_item_id):
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
        async with await self._lock(cache_item_id):
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
        lock = await self._lock(cache_item_id)
        if await lock.acquire(wait=wait):
            try:

                async def _setter(value: _CacheItemValueContraT) -> None:
                    await self._set(cache_item_id, value)

                yield await self._get(cache_item_id), _setter
                return
            finally:
                lock.release()
        yield None, None

    @override
    async def delete(self, cache_item_id: str) -> None:
        async with await self._lock(cache_item_id):
            await self._delete(cache_item_id)

    @abstractmethod
    async def _delete(self, cache_item_id: str) -> None:
        pass

    @override
    async def clear(self) -> None:
        async with MultiLock(self._locks_lock, *self._locks.values()):
            await self._clear()

    @abstractmethod
    async def _clear(self) -> None:
        pass
