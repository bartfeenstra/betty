"""
Job execution using async/await.
"""

from __future__ import annotations

from asyncio import CancelledError, Task, as_completed, get_running_loop
from contextlib import suppress
from typing import TYPE_CHECKING, TypeVar, final

from typing_extensions import override

from betty.job import Context
from betty.job.executor import Executor
from betty.job.scheduler import Cancelled, Completed

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler

_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


@final
class AsyncExecutor(Executor):
    """
    A job executor using async/await.
    """

    def __init__(self, scheduler: Scheduler[_ContextCoT], *, concurrency: int = 1):
        assert concurrency > 0
        self._scheduler = scheduler
        self._concurrency = concurrency
        self._working = False
        self._tasks: set[Task[None]] = set()

    @override
    async def start(self) -> None:
        if self._working:
            return
        self._working = True
        event_loop = get_running_loop()
        for _ in range(self._concurrency):
            task = event_loop.create_task(self._run_job())
            self._tasks.add(task)

    async def _run_job(self) -> None:
        with suppress(Completed, CancelledError):
            try:
                while self._working:
                    batch = await self._scheduler.get()
                    await batch()
            except Cancelled:
                await self.cancel()

    @override
    async def cancel(self) -> None:
        self._working = False
        for task in self._tasks:
            task.cancel()
        for task in as_completed(self._tasks):
            with suppress(CancelledError):
                await task

    @override
    async def complete(self) -> None:
        if not self._working:
            return
        for task in as_completed(self._tasks):
            with suppress(CancelledError):
                await task
        self._working = False
