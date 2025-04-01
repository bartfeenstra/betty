"""
Test utilities for :py:mod:`betty.job.executor`.
"""

from __future__ import annotations

from asyncio import sleep
from typing import TYPE_CHECKING, TypeVar

import pytest

from betty.job import Context
from betty.job.scheduler import Cancelled, ScheduledJobBatch, Scheduler
from betty.test_utils.job.scheduler import StaticScheduler

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.job.executor import Executor

_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


async def _sleep() -> None:
    await sleep(999)


class ExecutorTestBase:
    """
    A base class for testing :py:class:`betty.job.executor.Executor` implementations.
    """

    @pytest.fixture
    async def new_sut(self) -> Callable[[Scheduler[Context]], Executor]:
        """
        Provide the systems under test.
        """
        raise NotImplementedError

    async def test___aexit___with_scheduler_cancelled(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.__aexit__` implementations.
        """
        scheduler = StaticScheduler(Context(), [Cancelled()])
        async with new_sut(scheduler):
            pass

    async def test___aexit___with_scheduler_completed(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.__aexit__` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        async with new_sut(scheduler):
            pass

    async def test___aexit___with_arbitrary_exception(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.__aexit__` implementations.
        """
        exception = RuntimeError()
        scheduler = StaticScheduler(Context(), [_sleep for _ in range(999)])
        with pytest.raises(type(exception)) as exc_info:
            async with new_sut(scheduler):
                raise exception
        assert exc_info.value is exception

    async def test_start(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.start` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        sut = new_sut(scheduler)
        await sut.start()
        await sut.complete()

    async def test_start__when_started(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.start` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        sut = new_sut(scheduler)
        await sut.start()
        await sut.start()
        await sut.complete()

    @pytest.mark.parametrize(
        "batch_count",
        [
            1,
            999,
        ],
    )
    async def test_complete(
        self, batch_count: int, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.complete` implementations.
        """
        actual = []

        def _build_batch(batch_index: int) -> ScheduledJobBatch:
            async def _batch() -> None:
                actual.append(f"batch:{batch_index}")

            return _batch

        expected = [f"batch:{batch_index}" for batch_index in range(batch_count)]

        scheduler = StaticScheduler(
            Context(), [_build_batch(batch_index) for batch_index in range(batch_count)]
        )
        sut = new_sut(scheduler)
        await sut.start()
        await sut.complete()
        assert actual == expected

    async def test_complete__when_not_started(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.complete` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        sut = new_sut(scheduler)
        await sut.complete()

    async def test_complete__when_completed(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.complete` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        sut = new_sut(scheduler)
        await sut.start()
        await sut.complete()
        await sut.complete()

    async def test_cancel(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.cancel` implementations.
        """
        scheduler = StaticScheduler(Context(), [_sleep for _ in range(999)])
        sut = new_sut(scheduler)
        await sut.start()
        await sut.cancel()

    async def test_cancel__when_not_started(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.cancel` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        sut = new_sut(scheduler)
        await sut.cancel()

    async def test_cancel__when_cancelled(
        self, new_sut: Callable[[Scheduler[Context]], Executor]
    ) -> None:
        """
        Tests :py:meth:`betty.job.executor.Executor.cancel` implementations.
        """
        scheduler = StaticScheduler(Context(), [])
        sut = new_sut(scheduler)
        await sut.start()
        await sut.cancel()
        await sut.cancel()
