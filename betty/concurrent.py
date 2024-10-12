"""
Provide utilities for concurrent programming.
"""

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from asyncio import sleep
from collections import defaultdict
from collections.abc import Hashable
from types import TracebackType
from typing import Self, final, MutableMapping

from math import floor
from typing_extensions import override

from betty.typing import threadsafe


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
        pass

    @abstractmethod
    async def release(self) -> None:
        """
        Release the lock.
        """
        pass


async def asynchronize_acquire(lock: threading.Lock, *, wait: bool = True) -> bool:
    """
    Acquire a synchronous lock asynchronously.
    """
    while not lock.acquire(blocking=False):
        if not wait:
            return False
        # Sleeping for zero seconds does not actually sleep, but gives the event
        # loop a chance to progress other tasks while we wait for another chance
        # to acquire the lock.
        await sleep(0)
    return True


@final
class AsynchronizedLock(Lock):
    """
    Make a sychronous (blocking) lock asynchronous (non-blocking).
    """

    __slots__ = "_lock"

    def __init__(self, lock: threading.Lock):
        self._lock = lock

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
        return cls(threading.Lock())


@final
@threadsafe
class RateLimiter:
    """
    Rate-limit operations.

    This class implements the `Token Bucket algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_.
    """

    _PERIOD = 1

    def __init__(self, maximum: int):
        self._lock = AsynchronizedLock.threading()
        self._maximum = maximum
        self._available: int | float = maximum
        # A Token Bucket fills as time passes. However, we want callers to be able to start
        # using the limiter immediately, so we 'preload' the first's period's tokens, and
        # set the last added time to the end of the first period. This ensures there is no
        # needless waiting if the number of tokens consumed in total is less than the limit
        # per period.
        self._last_add = time.monotonic() + self._PERIOD

    def _add_tokens(self):
        now = time.monotonic()
        elapsed = now - self._last_add
        added = elapsed * self._maximum
        possibly_available = floor(self._available + added)
        if possibly_available > 0:
            self._available = min(possibly_available, self._maximum)
            self._last_add = now

    async def __aenter__(self) -> None:
        await self.wait()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return

    async def wait(self) -> None:
        """
        Wait until an operation may be performed (again).
        """
        async with self._lock:
            while self._available < 1:
                self._add_tokens()
                if self._available < 1:
                    await asyncio.sleep(0)
            self._available -= 1


class _Transaction(Lock):
    def __init__(
        self,
        transaction_id: Hashable,
        orchestrator_lock: Lock,
        ledger: MutableMapping[Hashable, bool],
    ):
        self._transaction_id = transaction_id
        self._ledger_lock = orchestrator_lock
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
        return not self._ledger[self._transaction_id]

    def _acquire(self) -> bool:
        self._ledger[self._transaction_id] = True
        return True

    @override
    async def release(self) -> None:
        self._ledger[self._transaction_id] = False


class Ledger:
    """
    Lazily create locks by keeping a ledger.

    The ledger lock is released once a transaction lock is acquired.
    """

    def __init__(self, ledger_lock: Lock):
        self._ledger_lock = ledger_lock
        self._ledger: MutableMapping[Hashable, bool] = defaultdict(lambda: False)

    def ledger(self, transaction_id: Hashable) -> Lock:
        """
        Ledger a new lock for the given transaction ID.
        """
        return _Transaction(transaction_id, self._ledger_lock, self._ledger)
