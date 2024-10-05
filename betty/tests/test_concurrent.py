import asyncio
import threading
import time
from asyncio import create_task, sleep, wait_for, gather

import pytest

from betty.concurrent import (
    RateLimiter,
    asynchronize_acquire,
    AsynchronizedLock,
)
from betty.test_utils.concurrent import DummyLock


class TestLock:
    async def test___aenter___and___aexit___with_acquisition(self) -> None:
        async with DummyLock(True):
            pass

    async def test___aenter___and___aexit___without_acquisition(self) -> None:
        sut = DummyLock(False)
        with pytest.raises(asyncio.TimeoutError):
            await wait_for(sut.__aenter__(), 0.000000001)


class TestAsynchronizeAcquire:
    async def test_should_acquire_immediately(self) -> None:
        lock = threading.Lock()
        assert await asynchronize_acquire(lock) is True
        assert lock.locked()
        lock.release()

    async def test_should_acquire_after_waiting(self) -> None:
        lock = threading.Lock()
        lock.acquire()
        task = create_task(asynchronize_acquire(lock))
        await sleep(1)
        lock.release()
        assert await task

    async def test_should_not_acquire_if_not_waiting(self) -> None:
        lock = threading.Lock()
        lock.acquire()
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()


class TestAsynchronizedLock:
    async def test_acquire_should_acquire_immediately(self) -> None:
        lock = threading.Lock()
        sut = AsynchronizedLock(lock)
        assert await sut.acquire()
        assert lock.locked()
        await sut.release()
        assert not lock.locked()

    async def test_acquire_should_acquire_after_waiting(self) -> None:
        lock = threading.Lock()
        sut = AsynchronizedLock(lock)
        lock.acquire()
        task = create_task(sut.acquire())
        await sleep(1)
        lock.release()
        assert await task

    async def test_acquire_should_not_acquire_if_not_waiting(self) -> None:
        lock = threading.Lock()
        sut = AsynchronizedLock(lock)
        lock.acquire()
        assert not await sut.acquire(wait=False)
        lock.release()


class TestRateLimiter:
    @pytest.mark.parametrize(
        ("expected", "iterations"),
        [
            (0, 100),
            # This is one higher than the rate limiter's maximum, to ensure we spend at least one full period.
            (1, 101),
        ],
    )
    async def test_wait(self, expected: int, iterations: int) -> None:
        sut = RateLimiter(100)

        async def _task() -> None:
            async with sut:
                pass

        start = time.time()
        await gather(*(_task() for _ in range(0, iterations)))
        end = time.time()
        duration = end - start
        assert expected == round(duration)
