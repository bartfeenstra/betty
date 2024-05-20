import logging
from collections import defaultdict
from collections.abc import Sequence, MutableMapping, AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Generic, Self, overload, AsyncContextManager, Literal

from betty.cache import (
    CacheItemValueCoT,
    Cache,
    CacheItem,
    CacheItemValueContraT,
    CacheItemValueSetter,
)
from betty.concurrent import _Lock, AsynchronizedLock, MultiLock
from betty.locale import Localizer


class _StaticCacheItem(CacheItem[CacheItemValueCoT], Generic[CacheItemValueCoT]):
    __slots__ = "_value", "_modified"

    def __init__(
        self,
        value: CacheItemValueCoT,
        modified: int | float | None = None,
    ):
        self._value = value
        self._modified = datetime.now().timestamp() if modified is None else modified

    async def value(self) -> CacheItemValueCoT:
        return self._value

    @property
    def modified(self) -> int | float:
        return self._modified


class _CommonCacheBase(Cache[CacheItemValueContraT], Generic[CacheItemValueContraT]):
    def __init__(
        self,
        localizer: Localizer,
        *,
        scopes: Sequence[str] | None = None,
    ):
        self._localizer = localizer
        self._scopes = scopes or ()
        self._scoped_caches: dict[str, Self] = {}
        self._locks: MutableMapping[str, _Lock] = defaultdict(
            AsynchronizedLock.threading
        )
        self._locks_lock = AsynchronizedLock.threading()

    async def _lock(self, cache_item_id: str) -> _Lock:
        async with self._locks_lock:
            return self._locks[cache_item_id]

    def with_scope(self, scope: str) -> Self:
        try:
            return self._scoped_caches[scope]
        except KeyError:
            self._scoped_caches[scope] = self._with_scope(scope)
            return self._scoped_caches[scope]

    def _with_scope(self, scope: str) -> Self:
        raise NotImplementedError

    @asynccontextmanager
    async def get(
        self, cache_item_id: str
    ) -> AsyncIterator[CacheItem[CacheItemValueContraT] | None]:
        async with await self._lock(cache_item_id):
            yield await self._get(cache_item_id)

    async def _get(self, cache_item_id: str) -> CacheItem[CacheItemValueContraT] | None:
        raise NotImplementedError

    async def set(
        self,
        cache_item_id: str,
        value: CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        async with await self._lock(cache_item_id):
            await self._set(cache_item_id, value, modified=modified)

    async def _set(
        self,
        cache_item_id: str,
        value: CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        raise NotImplementedError

    @overload
    def getset(
        self, cache_item_id: str
    ) -> AsyncContextManager[
        tuple[
            CacheItem[CacheItemValueContraT] | None,
            CacheItemValueSetter[CacheItemValueContraT],
        ]
    ]:
        pass  # pragma: no cover

    @overload
    def getset(
        self, cache_item_id: str, *, wait: Literal[False] = False
    ) -> AsyncContextManager[
        tuple[
            CacheItem[CacheItemValueContraT] | None,
            CacheItemValueSetter[CacheItemValueContraT] | None,
        ]
    ]:
        pass  # pragma: no cover

    @asynccontextmanager  # type: ignore[misc]
    async def getset(
        self, cache_item_id: str, *, wait: bool = True
    ) -> AsyncIterator[
        tuple[
            CacheItem[CacheItemValueContraT] | None,
            CacheItemValueSetter[CacheItemValueContraT] | None,
        ]
    ]:
        lock = await self._lock(cache_item_id)
        if await lock.acquire(wait=wait):
            try:

                async def _setter(value: CacheItemValueContraT) -> None:
                    await self._set(cache_item_id, value)

                yield await self._get(cache_item_id), _setter
                return
            finally:
                lock.release()
        yield None, None

    async def delete(self, cache_item_id: str) -> None:
        async with await self._lock(cache_item_id):
            await self._delete(cache_item_id)

    async def _delete(self, cache_item_id: str) -> None:
        raise NotImplementedError

    async def clear(self) -> None:
        async with MultiLock(self._locks_lock, *self._locks.values()):
            await self._clear()
        logger = logging.getLogger(__name__)
        if self._scopes:
            logger.info(
                self._localizer._('"{scope}" cache cleared.').format(
                    scope=".".join(self._scopes)
                )
            )
        else:
            logger.info(self._localizer._("All caches cleared."))

    async def _clear(self) -> None:
        raise NotImplementedError
