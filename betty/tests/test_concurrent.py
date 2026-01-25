import asyncio
import threading
import time
from asyncio import create_task, gather, run, sleep, wait_for
from typing import TypeVar
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.concurrent import AsynchronizedLock, Ledger, Lock, RateLimiter, backoff

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


async def test_backoff(mocker: MockerFixture) -> None:
    m_sleep = mocker.patch("asyncio.sleep")
    async for iteration in backoff():
        if iteration == 9:
            break

    assert m_sleep.call_count == 9
    m_sleep.assert_has_awaits(
        [
            call(0.001),
            call(0.002),
            call(0.004),
            call(0.008),
            call(0.016),
            call(0.032),
            call(0.064),
            call(0.128),
            call(0.128),
        ]
    )
