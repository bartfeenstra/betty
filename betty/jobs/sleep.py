"""
Jobs that sleep.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Final, final, override

from betty.job import Job

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.job.scheduler import Scheduler


@final
class Sleep(Job):
    """
    A job that sleeps.
    """

    default_duration: Final[int] = 999999999

    def __init__(
        self,
        job_id: str,
        duration: int = default_duration,
        /,
        *,
        dependencies: Iterable[str] = (),
        dependents: Iterable[str] = (),
        priority: bool = False,
    ):
        super().__init__(
            job_id, dependencies=dependencies, dependents=dependents, priority=priority
        )
        self._duration = duration

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await asyncio.sleep(self._duration)
