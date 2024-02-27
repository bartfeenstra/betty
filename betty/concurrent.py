"""
Provide utilities for concurrent programming.
"""
import asyncio
import time
from asyncio import sleep
from math import floor
from threading import Lock
from types import TracebackType


class AsynchronizedLock:
    """
    Make a sychronous (blocking) lock asynchronous (non-blocking).
    """

    def __init__(self, lock: Lock):
        self._lock = lock

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        self.release()

    async def acquire(self) -> None:
        while not self._lock.acquire(False):
            # Sleeping for zero seconds does not actually sleep, but gives the event
            # loop a chance to progress other tasks while we wait for another chance
            # to acquire the lock.
            await sleep(0)

    def release(self) -> None:
        self._lock.release()


class RateLimiter:
    """
    Rate-limit operations.

    This class implements the `Token Bucket algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_.
    """

    _PERIOD = 1

    def __init__(self, maximum: int):
        self._lock = AsynchronizedLock(Lock())
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

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        return

    async def wait(self) -> None:
        async with self._lock:
            while self._available < 1:
                self._add_tokens()
                if self._available < 1:
                    await asyncio.sleep(0.1)
            self._available -= 1
