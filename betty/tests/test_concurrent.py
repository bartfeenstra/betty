import asyncio
import multiprocessing
import os
import pickle
import threading
import time
from asyncio import create_task, sleep, wait_for, gather
from typing import TypeVar, Any

import pytest
from pytest_mock import MockerFixture
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
    Ledger,
    DefaultDict,
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


class TestLedger:
    async def test_ledger_with_wait_with_unlocked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.threading())
        lock = sut.ledger(transaction_id)
        assert await lock.acquire()
        await lock.release()

    async def test_ledger_without_wait_with_unlocked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.threading())
        lock = sut.ledger(transaction_id)
        assert await lock.acquire(wait=False)
        await lock.release()

    async def test_ledger_with_wait_with_locked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.threading())
        lock = sut.ledger(transaction_id)
        await lock.acquire()
        task = create_task(lock.acquire())
        await sleep(1)
        await lock.release()
        assert await task

    async def test_ledger_without_wait_with_locked(self) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(AsynchronizedLock.threading())
        lock = sut.ledger(transaction_id)
        await lock.acquire()
        assert not await lock.acquire(wait=False)
        await lock.release()

    def test_pickle(self, mocker: MockerFixture) -> None:
        mocker.patch("multiprocessing.context.assert_spawning")
        sut = Ledger(AsynchronizedLock.multiprocessing())
        pickle.loads(pickle.dumps(sut))


def _test_default_dict_process_target(sut: DefaultDict[_KeyT, Any], key: _KeyT):
    assert sut[key]


class TestDefaultDict:
    def _default_factory(self) -> int:
        return os.getpid()

    def _delayed_default_factory(self) -> int:
        time.sleep(2)
        return os.getpid()

    def test___delitem__(self) -> None:
        key = "my-first-key"
        sut = DefaultDict[str, int](self._default_factory)
        sut[key] = 123456789
        assert key in sut
        del sut[key]
        assert key not in list(sut)

    def test___getitem__(self) -> None:
        key = "my-first-key"
        value = 123456789
        sut = DefaultDict[str, int](self._default_factory)
        sut[key] = value
        assert sut[key] == value

    def test___getitem___should_create_default(self) -> None:
        sut = DefaultDict[str, int](self._default_factory)
        assert sut["my-first-key"] == os.getpid()

    def test___getitem___should_create_default_concurrently(self) -> None:
        key = "my-first-key"
        sut = DefaultDict[str, int](self._delayed_default_factory)
        process = multiprocessing.Process(
            target=_test_default_dict_process_target, args=(sut, key)
        )
        process.start()
        time.sleep(1)
        assert sut[key] != os.getpid()

    def test___iter__(self) -> None:
        key = "my-first-key"
        sut = DefaultDict[str, int](self._default_factory)
        sut[key] = 123456789
        assert list(iter(sut)) == [key]

    def test___len__(self) -> None:
        sut = DefaultDict[str, int](self._default_factory)
        sut["my-first-key"] = 123456789
        assert len(sut) == 1

    def test___setitem__(self) -> None:
        key = "my-first-key"
        value = 123456789
        sut = DefaultDict[str, int](self._default_factory)
        sut[key] = value
        assert sut[key] == value
