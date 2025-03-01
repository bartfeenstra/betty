import asyncio
import multiprocessing
import os
import pickle
import threading
import time
from asyncio import create_task, sleep, wait_for, gather
from multiprocessing.managers import SyncManager
from typing import TypeVar, Any

import pytest
from typing_extensions import override

from betty.concurrent import (
    RateLimiter,
    asynchronize_acquire,
    AsynchronizedLock,
    Lock,
    Ledger,
    DefaultDict,
    ensure_manager,
)
from betty.warnings import BettyDeprecationWarning

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
    async def test_should_acquire_immediately_with_threading(self) -> None:
        lock = threading.Lock()
        assert await asynchronize_acquire(lock)
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()

    async def test_should_acquire_immediately_with_multiprocessing(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        lock = multiprocessing_manager.Lock()
        assert await asynchronize_acquire(lock)
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()

    async def test_should_acquire_after_waiting_with_threading(self) -> None:
        lock = threading.Lock()
        lock.acquire()
        task = create_task(asynchronize_acquire(lock))
        await sleep(1)
        lock.release()
        assert await task

    async def test_should_acquire_after_waiting_with_multiprocessing(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        lock = multiprocessing_manager.Lock()
        lock.acquire()
        task = create_task(asynchronize_acquire(lock))
        await sleep(1)
        lock.release()
        assert await task

    async def test_should_not_acquire_if_not_waiting_with_threading(self) -> None:
        lock = threading.Lock()
        lock.acquire()
        assert not await asynchronize_acquire(lock, wait=False)
        lock.release()

    async def test_should_not_acquire_if_not_waiting_with_multiprocessing(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        lock = multiprocessing_manager.Lock()
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

    def test_lock(self) -> None:
        lock = threading.Lock()
        assert AsynchronizedLock(lock).lock is lock

    def test_threading(self) -> None:
        AsynchronizedLock.threading()


class TestRateLimiter:
    @pytest.mark.parametrize(
        ("expected", "iterations"),
        [
            (0, 100),
            # This is one higher than the rate limiter's maximum, to ensure we spend at least one full period.
            (1, 101),
        ],
    )
    async def test_wait(
        self, expected: int, iterations: int, multiprocessing_manager: SyncManager
    ) -> None:
        sut = RateLimiter(100, manager=multiprocessing_manager)

        async def _task() -> None:
            async with sut:
                pass

        start = time.time()
        await gather(*(_task() for _ in range(0, iterations)))
        end = time.time()
        duration = end - start
        assert expected == round(duration)

    async def test_is_available(self, multiprocessing_manager: SyncManager) -> None:
        sut = RateLimiter(1, 1, manager=multiprocessing_manager)

        await sut.wait()
        assert not await sut.is_available()
        await sleep(2)
        assert await sut.is_available()

    @classmethod
    def _test_wait_concurrently_target(cls, sut: RateLimiter):
        asyncio.run(sut.wait())

    async def test_wait_concurrently(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        sut = RateLimiter(1, 1, manager=multiprocessing_manager)

        process = multiprocessing.Process(
            target=self._test_wait_concurrently_target, args=(sut,)
        )
        process.start()

        await sleep(0.5)
        assert not await sut.is_available()
        await sleep(2)
        assert await sut.is_available()

    def test_pickle(self, multiprocessing_manager: SyncManager) -> None:
        sut = RateLimiter(1, manager=multiprocessing_manager)
        pickle.loads(pickle.dumps(sut))


class TestLedger:
    async def test_ledger_with_wait_with_unlocked(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(
            AsynchronizedLock(multiprocessing_manager.Lock()),
            manager=multiprocessing_manager,
        )
        lock = sut.ledger(transaction_id)
        assert await lock.acquire()
        await lock.release()

    async def test_ledger_without_wait_with_unlocked(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(
            AsynchronizedLock(multiprocessing_manager.Lock()),
            manager=multiprocessing_manager,
        )
        lock = sut.ledger(transaction_id)
        assert await lock.acquire(wait=False)
        await lock.release()

    async def test_ledger_with_wait_with_locked(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(
            AsynchronizedLock(multiprocessing_manager.Lock()),
            manager=multiprocessing_manager,
        )
        lock = sut.ledger(transaction_id)
        await lock.acquire()
        task = create_task(lock.acquire())
        await sleep(1)
        await lock.release()
        assert await task

    async def test_ledger_without_wait_with_locked(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        transaction_id = "my-first-transaction-id"
        sut = Ledger(
            AsynchronizedLock(multiprocessing_manager.Lock()),
            manager=multiprocessing_manager,
        )
        lock = sut.ledger(transaction_id)
        await lock.acquire()
        assert not await lock.acquire(wait=False)
        await lock.release()

    def test_pickle(self, multiprocessing_manager: SyncManager) -> None:
        sut = Ledger(
            AsynchronizedLock(multiprocessing_manager.Lock()),
            manager=multiprocessing_manager,
        )
        pickle.loads(pickle.dumps(sut))


def _test_default_dict_process_target(sut: DefaultDict[_KeyT, Any], key: _KeyT):
    assert sut[key]


class TestDefaultDict:
    def _default_factory(self) -> int:
        return os.getpid()

    def _delayed_default_factory(self) -> int:
        time.sleep(2)
        return os.getpid()

    def test___delitem__(self, multiprocessing_manager: SyncManager) -> None:
        key = "my-first-key"
        sut = DefaultDict[str, int](
            self._default_factory, manager=multiprocessing_manager
        )
        sut[key] = 123456789
        assert key in sut
        del sut[key]
        assert key not in list(sut)

    def test___getitem__(self, multiprocessing_manager: SyncManager) -> None:
        key = "my-first-key"
        value = 123456789
        sut = DefaultDict[str, int](
            self._default_factory, manager=multiprocessing_manager
        )
        sut[key] = value
        assert sut[key] == value

    def test___getitem___should_create_default(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        sut = DefaultDict[str, int](
            self._default_factory, manager=multiprocessing_manager
        )
        assert sut["my-first-key"] == os.getpid()

    def test___getitem___should_create_default_concurrently(
        self, multiprocessing_manager: SyncManager
    ) -> None:
        key = "my-first-key"
        sut = DefaultDict[str, int](
            self._delayed_default_factory, manager=multiprocessing_manager
        )
        process = multiprocessing.Process(
            target=_test_default_dict_process_target, args=(sut, key)
        )
        process.start()
        time.sleep(1)
        assert sut[key] != os.getpid()

    def test___iter__(self, multiprocessing_manager: SyncManager) -> None:
        key = "my-first-key"
        sut = DefaultDict[str, int](
            self._default_factory, manager=multiprocessing_manager
        )
        sut[key] = 123456789
        assert list(iter(sut)) == [key]

    def test___len__(self, multiprocessing_manager: SyncManager) -> None:
        sut = DefaultDict[str, int](
            self._default_factory, manager=multiprocessing_manager
        )
        sut["my-first-key"] = 123456789
        assert len(sut) == 1

    def test___setitem__(self, multiprocessing_manager: SyncManager) -> None:
        key = "my-first-key"
        value = 123456789
        sut = DefaultDict[str, int](
            self._default_factory, manager=multiprocessing_manager
        )
        sut[key] = value
        assert sut[key] == value


class TestEnsureManager:
    def test_with_manager(self) -> None:
        manager = SyncManager()
        assert ensure_manager(manager) is manager

    def test_without_manager(self) -> None:
        with pytest.warns(BettyDeprecationWarning):
            ensure_manager(None)
