"""
Test utilities for :py:mod:`betty.job`.
"""

from typing import TypeVar, final

from typing_extensions import override

from betty.job import Context, Job
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler import Scheduler
from betty.job.scheduler.default import DefaultScheduler
from betty.progress.no_op import NoOpProgress
from betty.user.no_op import NoOpUser

_ContextT = TypeVar("_ContextT", bound=Context)


@final
class NoOpJob(Job[Context]):
    """
    A job that does nothing.
    """

    @override
    async def do(self, scheduler: Scheduler[Context], /) -> None:
        pass


async def do(context: _ContextT, *jobs: Job[_ContextT]) -> None:
    """
    Do a number of jobs.
    """
    scheduler = DefaultScheduler(context, progress=NoOpProgress(), user=NoOpUser())
    async with AsyncExecutor(scheduler):
        await scheduler.add(*jobs)
        async with scheduler:
            pass
