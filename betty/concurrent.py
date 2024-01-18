"""
Provide utilities for concurrent programming.
"""
import asyncio
import threading
import time
from types import TracebackType


class RateLimiter:
    """
    Rate-limit tasks.

    This class implements the `Token Bucket algorithm <https://en.wikipedia.org/wiki/Token_bucket>`_.
    """

    def __init__(self, maximum: int):
        self._lock = asyncio.Lock()
        self._threading_lock = threading.Lock()
        self._maximum = maximum
        self._available: int | float = maximum
        self._last_add = time.monotonic()

    async def _add_tokens(self):
        now = time.monotonic()
        elapsed = now - self._last_add
        added = elapsed * self._maximum
        new = self._available + added
        if new > 0:
            self._available = min(new, self._maximum)
            self._last_add = now

    async def __aenter__(self) -> None:
        await self.wait()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        return

    async def wait(self):
        async with self._lock:
            with self._threading_lock:
                while self._available < 1:
                    await self._add_tokens()
                    if self._available < 1:
                        await asyncio.sleep(1)

                self._available -= 1
