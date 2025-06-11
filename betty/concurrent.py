"""
Provide utilities for concurrent programming.
"""

import asyncio
import multiprocessing
import threading as stdthreading
import time
from abc import ABC, abstractmethod
from asyncio import sleep
from collections.abc import Hashable, MutableMapping
from ctypes import c_longdouble
from math import floor
from multiprocessing.managers import SyncManager
from types import TracebackType
from typing import Self, TypeAlias, TypeVar, Union, final

from typing_extensions import override

from betty.typing import processsafe
from betty.warnings import deprecate

_KeyT = TypeVar("_KeyT")
_ValueT = TypeVar("_ValueT")


class Lock(ABC):
    """
    Provide an asynchronous lock.
    """

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.release()

    @abstractmethod
    async def acquire(self, *, wait: bool = True) -> bool:
        """
        Acquire the lock.
        """

    @abstractmethod
    async def release(self) -> None:
        """
        Release the lock.
        """


Acquirable: TypeAlias = Union[stdthreading.Lock, stdthreading.Semaphore]  # noqa: UP007


async def asynchronize_acquire(acquirable: Acquirable, *, wait: bool = True) -> bool:
    """
    Acquire a synchronous lock or semaphore asynchronously.
    """
    while not acquirable.acquire(blocking=False):
        if not wait:
            return False
        # Sleeping for zero seconds does not actually sleep, but gives the event
        # loop a chance to progress other tasks while we wait for another chance
        # to acquire the acquirable.
        await sleep(0)
    return True


@final
class AsynchronizedLock(Lock):
    """
    Make a synchronous (blocking) lock asynchronous (non-blocking).
    """

    __slots__ = "_lock"

    def __init__(self, lock: stdthreading.Lock):
        self._lock = lock

    @property
    def lock(self) -> stdthreading.Lock:
        """
        The underlying, synchronous lock.
        """
        return self._lock

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        return await asynchronize_acquire(self._lock, wait=wait)

    @override
    async def release(self) -> None:
        self._lock.release()

    @classmethod
    def threading(cls) -> Self:
        """
        Create a new thread-safe, asynchronous lock.
        """
        return cls(stdthreading.Lock())


class Semaphore(ABC):
    """
    An asynchronous semaphore.
    """

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.release()

    @abstractmethod
    async def acquire(self, *, wait: bool = True) -> bool:
        """
        Acquire the semaphore.
        """

    @abstractmethod
    async def release(self, n: int = 1) -> None:
        """
        Release the semaphore.
        """


@final
class AsynchronizedSemaphore(Semaphore):
    """
    Make a synchronous (blocking) semaphore asynchronous (non-blocking).
    """

    __slots__ = "_semaphore"

    def __init__(self, semaphore: stdthreading.Semaphore):
        self._semaphore = semaphore

    @property
    def semaphore(self) -> stdthreading.Semaphore:
        """
        The underlying, synchronous semaphore.
        """
        return self._semaphore

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        return await asynchronize_acquire(self._semaphore, wait=wait)

    @override
    async def release(self, n: int = 1) -> None:
        self._semaphore.release(n)

    @classmethod
    def threading(cls, n: int = 1) -> Self:
        """
        Create a new thread-safe, asynchronous semaphore.
        """
        return cls(stdthreading.Semaphore(n))


@final
@processsafe
class RateLimiter:
    """
    Rate-limit operations.

    This class implements the `Token Bucket algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_.
    """

    def __init__(
        self, maximum: int, period: int = 1, *, manager: SyncManager | None = None
    ):
        manager = ensure_manager(manager)
        self._lock = AsynchronizedLock(manager.Lock())
        self._maximum = maximum
        self._period = period
        self._available = manager.Value(c_longdouble, maximum)
        # A Token Bucket fills as time passes. However, we want callers to be able to start
        # using the limiter immediately, so we 'preload' the first's period's tokens, and
        # set the last added time to the end of the first period. This ensures there is no
        # needless waiting if the number of tokens consumed in total is less than the limit
        # per period.
        self._last_add = manager.Value(c_longdouble, time.monotonic() + self._period)

    def _add_tokens(self):
        now = time.monotonic()
        elapsed = now - self._last_add.value
        added = elapsed * self._maximum
        possibly_available = floor(self._available.value + added)
        if possibly_available > 0:
            self._available.value = min(possibly_available, self._maximum)
            self._last_add.value = now

    async def __aenter__(self) -> None:
        await self.wait()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return

    async def is_available(self) -> bool:
        """
        Whether an operation may be performed (again).
        """
        async with self._lock:
            self._add_tokens()
            return self._available.value != 0

    async def wait(self) -> None:
        """
        Wait until an operation may be performed (again).
        """
        async with self._lock:
            while self._available.value < 1:
                self._add_tokens()
                if self._available.value < 1:
                    await asyncio.sleep(0)
            self._available.value -= 1


class _Transaction(Lock):
    def __init__(
        self,
        transaction_id: Hashable,
        ledger_lock: Lock,
        ledger: MutableMapping[Hashable, bool],
    ):
        self._transaction_id = transaction_id
        self._ledger_lock = ledger_lock
        self._ledger = ledger

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        if wait:
            while True:
                async with self._ledger_lock:
                    if self._can_acquire():
                        return self._acquire()
                await sleep(0)
        else:
            async with self._ledger_lock:
                if self._can_acquire():
                    return self._acquire()
                return False

    def _can_acquire(self) -> bool:
        try:
            return not self._ledger[self._transaction_id]
        except KeyError:
            self._ledger[self._transaction_id] = False
            return True

    def _acquire(self) -> bool:
        self._ledger[self._transaction_id] = True
        return True

    @override
    async def release(self) -> None:
        self._ledger[self._transaction_id] = False


@processsafe
class Ledger:
    """
    Lazily create locks by keeping a ledger.

    The ledger lock is released once a transaction lock is acquired.
    """

    def __init__(self, ledger_lock: Lock, *, manager: SyncManager | None = None):
        manager = ensure_manager(manager)
        self._ledger_lock = ledger_lock
        self._ledger: MutableMapping[Hashable, bool] = manager.dict()

    def ledger(self, transaction_id: Hashable) -> Lock:
        """
        Ledger a new lock for the given transaction ID.
        """
        return _Transaction(transaction_id, self._ledger_lock, self._ledger)


def ensure_manager(manager: SyncManager | None, *, stacklevel: int = 1) -> SyncManager:
    """
    Ensure that a value is a multiprocessing manager.
    """
    if manager:
        return manager
    deprecate(
        "Not providing a multiprocessing manager is deprecated as of Betty 0.4.10.",
        stacklevel=stacklevel,
    )
    return multiprocessing.Manager()
