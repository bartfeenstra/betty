"""
Jobs that do nothing.
"""

from typing import final, override

from betty.job import Job
from betty.job.scheduler import Scheduler


@final
class NoOp(Job):
    """
    A job that does nothing.
    """

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        return
