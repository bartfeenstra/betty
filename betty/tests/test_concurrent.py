import time
from asyncio import create_task, sleep
from threading import Lock

import pytest

from betty.asyncio import gather
from betty.concurrent import (
    RateLimiter,
    asynchronize_acquire,
    MultiLock,
    AsynchronizedLock,
)


class TestAsynchronizeAcquire:
    async def test_should_acquire_immediately(self) -> None:
        lock = Lock()
        assert await asynchronize_acquire(lock) is True
        assert lock.locked()
        lock.release()

    async def test_should_acquire_after_waiting(self) -> None:
        lock = Lock()
        lock.acquire()
        task = create_task(asynchronize_acquire(lock))
        await sleep(1)
        lock.release()
        assert await task

    async def test_should_not_acquire_if_not_waiting(self) -> None:
        lock = Lock()
        lock.acquire()
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()


class TestAsynchronizedLock:
    async def test_acquire_should_acquire_immediately(self) -> None:
        lock = Lock()
        sut = AsynchronizedLock(lock)
        assert await sut.acquire()
        assert lock.locked()
        sut.release()
        assert not lock.locked()

    async def test_acquire_should_acquire_after_waiting(self) -> None:
        lock = Lock()
        sut = AsynchronizedLock(lock)
        lock.acquire()
        task = create_task(sut.acquire())
        await sleep(1)
        lock.release()
        assert await task

    async def test_acquire_should_not_acquire_if_not_waiting(self) -> None:
        lock = Lock()
        sut = AsynchronizedLock(lock)
        lock.acquire()
        assert not await sut.acquire(wait=False)
        lock.release()


class TestMultiLock:
    async def test_acquire_should_acquire_immediately(self) -> None:
        locks = (
            Lock(),
            Lock(),
            Lock(),
        )
        sut = MultiLock(*(AsynchronizedLock(lock) for lock in locks))
        assert await sut.acquire() is True
        for lock in locks:
            assert lock.locked()
        sut.release()
        for lock in locks:
            assert not lock.locked()

    async def test_acquire_should_not_acquire_if_not_waiting(self) -> None:
        sentinel = Lock()
        locks = (
            Lock(),
            Lock(),
            Lock(),
        )
        sut = MultiLock(*(AsynchronizedLock(lock) for lock in (*locks, sentinel)))
        sentinel.acquire()
        assert await sut.acquire(wait=False) is False
        for lock in locks:
            assert not lock.locked()


class TestRateLimiter:
    @pytest.mark.parametrize(
        "expected, iterations",
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
