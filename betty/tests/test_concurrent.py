import asyncio
import multiprocessing
import pickle
import threading
import time
from asyncio import create_task, gather, sleep, wait_for
from multiprocessing.managers import SyncManager
from typing import TypeVar, cast

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


@pytest.fixture(
    params=[
        lambda _: threading.Lock(),
        lambda _: threading.Semaphore(),
        lambda multiprocessing_manager: multiprocessing_manager.Lock(),
        lambda multiprocessing_manager: multiprocessing_manager.Semaphore(),
    ]
)
def acquirable(
    multiprocessing_manager: SyncManager, request: pytest.FixtureRequest
) -> Acquirable:
    """
    Produce :py:class:`betty.concurrent.Acquirable` instances.
    """
    return cast(Acquirable, request.param(multiprocessing_manager))


async def test_asynchronize_acquire__should_acquire_immediately(
    acquirable: Acquirable,
) -> None:
    assert await asynchronize_acquire(acquirable)
    assert not await asynchronize_acquire(acquirable, wait=False)
    acquirable.release()


async def test_asynchronize_acquire__should_acquire_after_waiting(
    acquirable: Acquirable,
) -> None:
    acquirable.acquire()
    task = create_task(asynchronize_acquire(acquirable))
    await sleep(1)
    acquirable.release()
    assert await task


async def test_asynchronize_acquire__should_not_acquire_if_not_waiting(
    acquirable: Acquirable,
) -> None:
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
        AsynchronizedLock.threading()


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
        AsynchronizedSemaphore.threading()


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
        await gather(*(_task() for _ in range(iterations)))
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
    async def test_ledger__with_wait_with_unlocked(
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

    async def test_ledger__without_wait_with_unlocked(
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

    async def test_ledger__with_wait_with_locked(
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

    async def test_ledger__without_wait_with_locked(
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


def test_ensure_manager__with_manager() -> None:
    manager = SyncManager()
    assert ensure_manager(manager) is manager


def test_ensure_manager__without_manager() -> None:
    with pytest.warns(BettyDeprecationWarning):
        ensure_manager(None)
