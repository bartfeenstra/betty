"""
Test utilities for :py:mod:`betty.job`.
"""

from betty.job import Job
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler.default import DefaultScheduler
from betty.user.no_op import NoOpUser


async def do(*jobs: Job) -> None:
    """
    Do a number of jobs.
    """
    scheduler = DefaultScheduler(user=NoOpUser())
    async with AsyncExecutor(scheduler):
        await scheduler.add(*jobs)
        async with scheduler:
            pass
