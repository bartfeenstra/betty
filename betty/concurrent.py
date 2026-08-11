"""
Provide utilities for concurrent programming.
"""

from __future__ import annotations

import asyncio
import threading
import time
from abc import ABCMeta, abstractmethod
from asyncio import sleep
from math import floor
from typing import TYPE_CHECKING, Final, final, override

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Hashable, MutableMapping
    from types import TracebackType

max_strands: Final[int] = 64


class Lock(metaclass=ABCMeta):
    """
    Provide an asynchronous lock.
    """

    @final
    async def __aenter__(self):
        await self.acquire()

    @final
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


@final
class ThreadSafeLock(Lock):
    """
    An asynchronous thread-safe lock.
    """

    __slots__ = ("_lock",)

    def __init__(self, lock: threading.Lock | None = None, /):
        self.lock: Final[threading.Lock] = lock or threading.Lock()
        """
        The underlying, synchronous lock.
        """

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        async for _ in backoff():
            if self.lock.acquire(blocking=False):
                return True
            if wait:
                continue
            return False
        # This never happens, because backoff() is an infinite generator.
        raise NotImplementedError

    @override
    async def release(self) -> None:
        self.lock.release()


@final
class RateLimiter:
    """
    Rate-limit operations.

    This class implements the `Token Bucket algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_.
    """

    def __init__(self, maximum: int, period: int = 1, /):
        self._lock = ThreadSafeLock()
        self._maximum = maximum
        self._period = period
        self._available = maximum
        # A Token Bucket fills as time passes. However, we want callers to be able to start
        # using the limiter immediately, so we 'preload' the first's period's tokens, and
        # set the last added time to the end of the first period. This ensures there is no
        # needless waiting if the number of tokens consumed in total is less than the limit
        # per period.
        self._last_add = time.monotonic() + self._period

    def _add_tokens(self) -> None:
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

    async def is_available(self) -> bool:
        """
        Whether an operation may be performed (again).
        """
        async with self._lock:
            self._add_tokens()
            return self._available != 0

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


class Ledger:
    """
    Lazily create locks by keeping a ledger.

    The ledger lock is released once a transaction lock is acquired.
    """

    def __init__(self, ledger_lock: Lock):
        self._ledger_lock = ledger_lock
        self._ledger: MutableMapping[Hashable, bool] = {}

    def ledger(self, transaction_id: Hashable) -> Lock:
        """
        Ledger a new lock for the given transaction ID.
        """
        return _Transaction(transaction_id, self._ledger_lock, self._ledger)


async def backoff() -> AsyncIterator[int]:
    """
    Implement `exponential backoff <https://en.wikipedia.org/wiki/Exponential_backoff>`__.

    The returned iterator sleeps after every iteration, increasing the duration with every iteration, up to a limit.

    Usage:

    .. code-block:: python

       async for iteration in backoff():
         if success:
            return  # Or break.
    """
    iterations = 0
    while True:
        yield iterations
        await asyncio.sleep(0.001 * 2 ** min(iterations, 7))
        iterations += 1
