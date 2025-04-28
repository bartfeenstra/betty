from abc import abstractmethod
from collections.abc import AsyncIterator, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import datetime
from multiprocessing.managers import SyncManager
from typing import (
    Any,
    Generic,
    Literal,
    Protocol,
    Self,
    TypeVar,
    overload,
)

from typing_extensions import override

from betty.cache import Cache, CacheItem, CacheItemValueSetter
from betty.concurrent import AsynchronizedLock, Ledger, ensure_manager
from betty.typing import processsafe

_CacheT = TypeVar("_CacheT", bound=Cache[Any])
_CacheItemValueCoT = TypeVar("_CacheItemValueCoT", covariant=True)
_CacheItemValueContraT = TypeVar("_CacheItemValueContraT", contravariant=True)


class _CommonCacheBaseGetter(Generic[_CacheItemValueCoT], Protocol):
    async def __call__(
        self, cache_item_id: str
    ) -> CacheItem[_CacheItemValueCoT] | None:
        pass


class _CommonCacheBaseSetter(Generic[_CacheItemValueContraT], Protocol):
    async def __call__(
        self,
        cache_item_id: str,
        value: _CacheItemValueContraT,
        *,
        modified: int | float | None = None,
    ) -> None:
        pass


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


@processsafe
class _CommonCacheBase(Cache[_CacheItemValueContraT], Generic[_CacheItemValueContraT]):
    def __init__(
        self,
        *,
        scopes: Sequence[str] | None = None,
        manager: SyncManager | _CommonCacheBaseState[Self] | None = None,
    ):
        self._scopes = scopes or ()
        if isinstance(manager, _CommonCacheBaseState):
            self._cache_lock = manager.cache_lock
            self._cache_item_lock_ledger = manager.cache_item_lock_ledger
        else:
            manager = ensure_manager(manager)
            self._cache_lock = AsynchronizedLock(manager.Lock())
            self._cache_item_lock_ledger = Ledger(self._cache_lock, manager=manager)

    @override
    @asynccontextmanager
    async def get(
        self, cache_item_id: str
    ) -> AsyncIterator[CacheItem[_CacheItemValueContraT] | None]:
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
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
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
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
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT],
        ]
    ]:
        pass

    @overload
    def getset(
        self, cache_item_id: str, *, wait: Literal[False] = False
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        pass

    def getset(
        self, cache_item_id: str, *, wait: bool = True
    ) -> AbstractAsyncContextManager[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        return self._getset(cache_item_id, self._get, self._set, wait=wait)

    @asynccontextmanager
    async def _getset(
        self,
        cache_item_id: str,
        getter: _CommonCacheBaseGetter[_CacheItemValueContraT],
        setter: _CommonCacheBaseSetter[_CacheItemValueContraT],
        *,
        wait: bool = True,
    ) -> AsyncIterator[
        tuple[
            CacheItem[_CacheItemValueContraT] | None,
            CacheItemValueSetter[_CacheItemValueContraT] | None,
        ]
    ]:
        lock = self._cache_item_lock_ledger.ledger(cache_item_id)
        if await lock.acquire(wait=wait):
            try:

                async def _setter(value: _CacheItemValueContraT) -> None:
                    await setter(cache_item_id, value)

                yield await getter(cache_item_id), _setter
                return
            finally:
                await lock.release()
        yield None, None

    @override
    async def delete(self, cache_item_id: str) -> None:
        async with self._cache_item_lock_ledger.ledger(cache_item_id):
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
