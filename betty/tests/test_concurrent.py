import asyncio
import multiprocessing
import threading
import time
from asyncio import create_task, sleep, wait_for, gather

import pytest
from typing_extensions import override

from betty.concurrent import (
    RateLimiter,
    asynchronize_acquire,
    AsynchronizedLock,
    Lock,
    acquire,
    Lockey,
    ThreadingLockType,
    MultiprocessingLockType,
)


class _LockTestDummyLock(Lock):
    def __init__(self, acquire: bool):
        self._acquire = acquire

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        if self._acquire:
            return True
        await sleep(999999999)
        return False  # pragma: nocover

    @override
    async def release(self) -> None:
        pass


class TestLock:
    async def test___aenter___and___aexit___with_acquisition(self) -> None:
        async with _LockTestDummyLock(True):
            pass

    async def test___aenter___and___aexit___without_acquisition(self) -> None:
        sut = _LockTestDummyLock(False)
        with pytest.raises(asyncio.TimeoutError):
            await wait_for(sut.__aenter__(), 0.000000001)


class TestAsynchronizeAcquire:
    @pytest.mark.parametrize(
        "lock",
        [
            threading.Lock(),
            multiprocessing.Lock(),
        ],
    )
    async def test_should_acquire_immediately(self, lock: Lockey) -> None:
        assert await asynchronize_acquire(lock)
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()

    @pytest.mark.parametrize(
        "lock",
        [
            threading.Lock(),
            multiprocessing.Lock(),
        ],
    )
    async def test_should_acquire_after_waiting(self, lock: Lockey) -> None:
        lock.acquire()
        task = create_task(asynchronize_acquire(lock))
        await sleep(1)
        lock.release()
        assert await task

    @pytest.mark.parametrize(
        "lock",
        [
            threading.Lock(),
            multiprocessing.Lock(),
        ],
    )
    async def test_should_not_acquire_if_not_waiting(self, lock: Lockey) -> None:
        lock.acquire()
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()


class TestAcquire:
    @pytest.mark.parametrize(
        "lock",
        [
            threading.Lock(),
            multiprocessing.Lock(),
        ],
    )
    def test_should_acquire_immediately(self, lock: Lockey) -> None:
        assert acquire(lock) is True
        assert not acquire(lock, wait=False)
        lock.release()

    @pytest.mark.parametrize(
        "lock",
        [
            threading.Lock(),
            multiprocessing.Lock(),
        ],
    )
    def test_should_not_acquire_if_not_waiting(self, lock: Lockey) -> None:
        lock.acquire()
        assert not acquire(lock, wait=False)
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

    def test_lock(self) -> None:
        lock = threading.Lock()
        assert AsynchronizedLock(lock).lock is lock

    def test_threading(self) -> None:
        sut = AsynchronizedLock.threading()
        assert isinstance(sut.lock, ThreadingLockType)

    def test_multiprocessing(self) -> None:
        sut = AsynchronizedLock.multiprocessing()
        assert isinstance(sut.lock, MultiprocessingLockType)


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
