"""
Provide utilities for concurrent programming.
"""

import asyncio
import threading
import time
from asyncio import sleep
from math import floor
from threading import Lock
from types import TracebackType
from typing import Self

from typing_extensions import override

from betty.asyncio import gather


class _Lock:
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
        self.release()

    async def acquire(self, *, wait: bool = True) -> bool:
        """
        Acquire the lock.
        """
        raise NotImplementedError

    def release(self) -> None:
        """
        Release the lock.
        """
        raise NotImplementedError


async def asynchronize_acquire(lock: Lock, *, wait: bool = True) -> bool:
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


class AsynchronizedLock(_Lock):
    """
    Make a sychronous (blocking) lock asynchronous (non-blocking).
    """

    __slots__ = "_lock"

    def __init__(self, lock: Lock):
        self._lock = lock

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        return await asynchronize_acquire(self._lock, wait=wait)

    @override
    def release(self) -> None:
        self._lock.release()

    @classmethod
    def threading(cls) -> Self:
        """
        Create a new thread-safe, asynchronous lock.
        """
        return cls(threading.Lock())


class MultiLock(_Lock):
    """
    Provide a lock that only acquires if all of the given locks can be acquired.
    """

    __slots__ = "_locked", "_locks"

    def __init__(self, *locks: _Lock):
        self._locks = locks
        self._locked = False

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        acquisitions = await gather(*(lock.acquire(wait=wait) for lock in self._locks))
        # We require all locks to be acquired, or none at all
        # If one or more fail, release the others.
        if False in acquisitions:
            for lock, acquisition in zip(self._locks, acquisitions):
                if acquisition:
                    lock.release()
            return False
        self._locked = True
        return True

    @override
    def release(self) -> None:
        self._locked = False
        for lock in self._locks:
            lock.release()


class RateLimiter:
    """
    Rate-limit operations.

    This class implements the `Token Bucket algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_.

    This class is thread-safe.
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
                    await asyncio.sleep(0.1)
            self._available -= 1
