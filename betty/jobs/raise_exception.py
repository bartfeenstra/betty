"""
Jobs that raise exceptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.job import Job

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.job.scheduler import Scheduler


@final
class RaiseException(Job):
    """
    A job that raises an exception.
    """

    def __init__(
        self,
        job_id: str,
        /,
        *,
        reason: BaseException,
        dependencies: Iterable[str] = (),
        dependents: Iterable[str] = (),
        priority: bool = False,
    ):
        super().__init__(
            job_id, dependencies=dependencies, dependents=dependents, priority=priority
        )
        self._reason = reason

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        raise self._reason
