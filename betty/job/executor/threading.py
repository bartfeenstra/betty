"""
Job execution using thread pools.
"""

from __future__ import annotations

import asyncio
from asyncio import Task, gather, get_running_loop
from concurrent import futures
from contextlib import suppress
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.job.executor import Executor
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler import Cancelled, Scheduler

if TYPE_CHECKING:
    from collections.abc import MutableSequence
    from concurrent.futures import Future

    from betty.job import Context


@final
class ThreadPoolExecutor(Executor):
    """
    A job executor using a thread pool.
    """

    def __init__(
        self,
        scheduler: Scheduler[Context],
        *,
        async_concurrency: int = 1,
        threading_concurrency: int = 1,
    ):
        assert async_concurrency > 0
        assert threading_concurrency > 0
        self._scheduler = scheduler
        self._async_concurrency = async_concurrency
        self._threading_concurrency = threading_concurrency
        self._working = False
        self._futures: set[Future[None]] = set()
        self._tasks: set[Task[None]] = set()
        self._thread_pool = futures.ThreadPoolExecutor(
            max_workers=threading_concurrency
        )
        self._event_loop = get_running_loop()
        self._async_executors: MutableSequence[Executor] = []

    @override
    async def start(self) -> None:
        if self._working:
            return
        self._working = True
        for _ in range(self._threading_concurrency):
            self._futures.add(self._thread_pool.submit(self._run_job))

    def _run_job(self) -> None:
        self._tasks.add(self._event_loop.create_task(self.__run_job()))

    async def __run_job(self) -> None:
        async_executor = AsyncExecutor(
            self._scheduler, concurrency=self._async_concurrency
        )
        self._async_executors.append(async_executor)
        try:
            async with async_executor:
                pass
        except Cancelled:
            await self.cancel()

    @override
    async def cancel(self) -> None:
        self._working = False
        await gather(
            *[async_executor.cancel() for async_executor in self._async_executors]
        )
        for task in self._tasks:
            task.cancel()
        for future in self._futures:
            future.cancel()
        self._thread_pool.shutdown(False, cancel_futures=True)

    @override
    async def complete(self) -> None:
        if not self._working:
            return
        await gather(
            *[async_executor.complete() for async_executor in self._async_executors]
        )
        for task in asyncio.as_completed(self._tasks):
            with suppress(asyncio.CancelledError):
                await task
        for future in futures.as_completed(self._futures):
            with suppress(futures.CancelledError):
                future.result()
        self._thread_pool.shutdown()
        self._working = False
