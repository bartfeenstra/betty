import asyncio
import threading
import time
from asyncio import create_task, gather, run, sleep, wait_for
from collections.abc import Iterable
from typing import TypeVar

import pytest
from typing_extensions import override

from betty.concurrent import (
    Acquirable,
    AsynchronizedLock,
    AsynchronizedSemaphore,
    Ledger,
    Lock,
    RateLimiter,
    Semaphore,
    asynchronize_acquire,
)

_KeyT = TypeVar("_KeyT")


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
    async def test___aenter____and___aexit___with_acquisition(self) -> None:
        async with _LockTestDummyLock(True):
            pass

    async def test___aenter____and___aexit___without_acquisition(self) -> None:
        sut = _LockTestDummyLock(False)
        with pytest.raises(asyncio.TimeoutError):
            await wait_for(sut.__aenter__(), 0.000000001)


class _SemaphoreTestDummySemaphore(Semaphore):
    def __init__(self, n: int, acquire: bool):
        self._n = n
        self._acquire = acquire

    @override
    async def acquire(self, *, wait: bool = True) -> bool:
        if self._acquire:
            self._n -= 1
            return True
        await sleep(999999999)
        return False  # pragma: nocover

    @override
    async def release(self, n: int = 1) -> None:
        self._n += n


class TestSemaphore:
    async def test___aenter____and___aexit___with_acquisition(self) -> None:
        async with _SemaphoreTestDummySemaphore(1, True):
            pass

    async def test___aenter____and___aexit___without_acquisition(self) -> None:
        sut = _SemaphoreTestDummySemaphore(1, False)
        with pytest.raises(asyncio.TimeoutError):
            await wait_for(sut.__aenter__(), 0.000000001)


@pytest.fixture
def acquirables() -> Iterable[Acquirable]:
    return [
        threading.Lock(),
        threading.Semaphore(),
    ]


async def test_asynchronize_acquire__should_acquire_immediately(
    acquirables: Iterable[Acquirable],
) -> None:
    for acquirable in acquirables:
        assert await asynchronize_acquire(acquirable)
        assert not await asynchronize_acquire(acquirable, wait=False)
        acquirable.release()


async def test_asynchronize_acquire__should_acquire_after_waiting(
    acquirables: Iterable[Acquirable],
) -> None:
    for acquirable in acquirables:
        acquirable.acquire()
        task = create_task(asynchronize_acquire(acquirable))
        await sleep(1)
        acquirable.release()
        assert await task


async def test_asynchronize_acquire__should_not_acquire_if_not_waiting(
    acquirables: Iterable[Acquirable],
) -> None:
    for acquirable in acquirables:
        acquirable.acquire()
        assert not await asynchronize_acquire(acquirable, wait=False)
        acquirable.release()


class TestAsynchronizedLock:
    async def test_acquire__should_acquire_immediately(self) -> None:
        lock = threading.Lock()
        sut = AsynchronizedLock(lock)
        assert await sut.acquire()
        assert lock.locked()
        await sut.release()
        assert not lock.locked()

    async def test_acquire__should_acquire_after_waiting(self) -> None:
        lock = threading.Lock()
        sut = AsynchronizedLock(lock)
        lock.acquire()
        task = create_task(sut.acquire())
        await sleep(1)
        lock.release()
        assert await task

    async def test_acquire__should_not_acquire_if_not_waiting(self) -> None:
        lock = threading.Lock()
        sut = AsynchronizedLock(lock)
        lock.acquire()
        assert not await sut.acquire(wait=False)
        lock.release()

    def test_lock(self) -> None:
        lock = threading.Lock()
        assert AsynchronizedLock(lock).lock is lock

    def test_threading(self) -> None:
        AsynchronizedLock.new_threadsafe()


class TestAsynchronizedSemaphore:
    async def test_acquire__should_acquire_immediately(self) -> None:
        semaphore = threading.Semaphore()
        sut = AsynchronizedSemaphore(semaphore)
        assert await sut.acquire(wait=False)
        await sut.release()

    async def test_acquire__should_acquire_after_waiting(self) -> None:
        semaphore = threading.Semaphore()
        sut = AsynchronizedSemaphore(semaphore)
        semaphore.acquire(blocking=False)
        task = create_task(sut.acquire())
        await sleep(1)
        semaphore.release()
        assert await task

    async def test_acquire__should_not_acquire_if_not_waiting(self) -> None:
        semaphore = threading.Semaphore()
        sut = AsynchronizedSemaphore(semaphore)
        semaphore.acquire(blocking=False)
        assert not await sut.acquire(wait=False)
        semaphore.release()

    async def test_release(self) -> None:
        semaphore = threading.Semaphore(2)
        sut = AsynchronizedSemaphore(semaphore)
        assert await sut.acquire(wait=False)
        assert await sut.acquire(wait=False)
        await sut.release()
        assert await sut.acquire(wait=False)
        # @todo this should error
        assert not await sut.acquire(wait=False)
        await sut.release()
        await sut.release()

    def test_semaphore(self) -> None:
        semaphore = threading.Semaphore()
        assert AsynchronizedSemaphore(semaphore).semaphore is semaphore

    def test_threading(self) -> None:
        AsynchronizedSemaphore.new_threadsafe()


class TestRateLimiter:
    _TEST_WAIT_PARAMETERS = [
        (0, 100, 100),
        # This is one higher than the rate limiter's maximum, to ensure we spend at least one full period.
        (1, 101, 100),
    ]

    @pytest.mark.parametrize(
        ("expected", "consumers", "maximum"),
        _TEST_WAIT_PARAMETERS,
    )
    async def test_wait(self, expected: int, consumers: int, maximum: int) -> None:
        sut = RateLimiter(maximum)

        async def _task() -> None:
            async with sut:
                pass

        start = time.time()
        await gather(*(_task() for _ in range(consumers)))
        end = time.time()
        duration = end - start
        assert duration >= expected

    @classmethod
    def _consume(cls, sut: RateLimiter) -> None:
        run(cls.__consume(sut))

    @classmethod
    async def __consume(cls, sut: RateLimiter) -> None:
        async with sut:
            pass

    async def test_is_available(self) -> None:
        sut = RateLimiter(1, 1)

        await sut.wait()
        assert not await sut.is_available()
        await sleep(2)
        assert await sut.is_available()


class TestLedger:
    async def test_ledger__with_wait_with_unlocked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.new_threadsafe())
        lock = sut.ledger(transaction_id)
        assert await lock.acquire()
        await lock.release()

    async def test_ledger__without_wait_with_unlocked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.new_threadsafe())
        lock = sut.ledger(transaction_id)
        assert await lock.acquire(wait=False)
        await lock.release()

    async def test_ledger__with_wait_with_locked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.new_threadsafe())
        lock = sut.ledger(transaction_id)
        await lock.acquire()
        task = create_task(lock.acquire())
        await sleep(1)
        await lock.release()
        assert await task

    async def test_ledger__without_wait_with_locked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.new_threadsafe())
        lock = sut.ledger(transaction_id)
        await lock.acquire()
        assert not await lock.acquire(wait=False)
        await lock.release()
