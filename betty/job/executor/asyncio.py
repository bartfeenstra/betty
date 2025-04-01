"""
Job execution using async/await.
"""

from __future__ import annotations

from asyncio import Task, TaskGroup
from contextlib import AsyncExitStack, suppress
from typing import TYPE_CHECKING, TypeVar, final

from typing_extensions import override

from betty.job import Context
from betty.job.executor import Executor
from betty.job.scheduler import Closed

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
        self._exit_stack = AsyncExitStack()

    @override
    async def start(self) -> None:
        if self._working:
            return
        self._working = True
        task_group = TaskGroup()
        await self._exit_stack.enter_async_context(task_group)
        for _ in range(self._concurrency):
            task = task_group.create_task(self._run_job())
            self._tasks.add(task)

    async def _run_job(self) -> None:
        with suppress(Closed):
            while self._working:
                batch = await self._scheduler.get()
                await batch()

    @override
    async def cancel(self) -> None:
        self._working = False
        for task in self._tasks:
            task.cancel()
        await self._exit_stack.aclose()

    @override
    async def complete(self) -> None:
        if not self._working:
            return
        await self._exit_stack.aclose()
        self._working = False
