"""
Jobs that do nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
class NoOpJob(Job):
    """
    A job that does nothing.
    """

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        return
