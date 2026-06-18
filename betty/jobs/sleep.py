"""
Jobs that sleep.
"""

from __future__ import annotations

from asyncio import sleep
from typing import TYPE_CHECKING, final, override

from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
class Sleep(Job):
    """
    A job that sleeps for a long, long time.
    """

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await sleep(999999999)
