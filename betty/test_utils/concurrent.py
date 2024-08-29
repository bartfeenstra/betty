"""
Test utilities for :py:mod:`betty.concurrent`.
"""

from asyncio import sleep
from typing_extensions import override

from betty.concurrent import Lock


class DummyLock(Lock):
    """
    A dummy :py:class:`betty.concurrent.Lock` implementation.
    """

    def __init__(self, acquire: bool):
        self._acquire = acquire

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        if not wait:
            return self._acquire
        if self._acquire:
            return True
        await sleep(999999999)
        return False

    @override
    async def release(self) -> None:
        pass
