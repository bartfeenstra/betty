"""
Job scheduling.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Final, Self, final

from betty.job import Context

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import TracebackType

    from betty.job import Job

type ScheduledJobBatch = Callable[[], Awaitable[None]]
"""
A callable to call one or more jobs.

The callable MUST cancel the scheduler if an error is raised.
"""


class Closed(Exception):
    """
    Raised when a scheduler is closed.
    """


class Cancelled(Closed):
    """
    Raised when a scheduler has cancelled.
    """


class Released(Exception):
    """
    Raised when a scheduler has been released.
    """


@final
class CyclicDependencyError(Cancelled):
    """
    Raised when a scheduler has cancelled due to a cyclic dependency.
    """

    def __init__(self, job_ids: Sequence[str], /):
        assert job_ids
        cycle = " -> ".join(f'"{job_id}"' for job_id in job_ids)
        super().__init__(f'Job "{job_ids[0]}" has cyclic dependencies: {cycle}.')


@final
class UnknownJobError(Cancelled):
    """
    Raised when a scheduler has cancelled due to an unknown job.
    """

    def __init__(self, job_id: str, /):
        super().__init__(f'Job "{job_id}" was never added.')


@final
class DuplicateJobError(Cancelled):
    """
    Raised when a scheduler cannot add the same job (ID) more than once.
    """

    def __init__(self, job_id: str, /):
        super().__init__(
            f'Job "{job_id}" was added already, and cannot be added again.'
        )


@final
class Completed(Closed):
    """
    Raised when a scheduler has completed.
    """


class Scheduler(metaclass=ABCMeta):
    """
    A job scheduler.
    """

    def __init__(self, context: Context | None = None, /):
        self.context: Final[Context] = Context() if context is None else context
        """
        The context for all jobs in this scheduler.
        """

    @abstractmethod
    async def add(self, *jobs: Job) -> None:
        """
        Add a new job.
        """

    @abstractmethod
    async def release(self) -> None:
        """
        Release the scheduler.

        Once called, jobs are released by :py:meth:`betty.job.scheduler.Scheduler.get`, and
        new jobs with dependents can no longer be added.
        """

    @abstractmethod
    async def get(self) -> ScheduledJobBatch:
        """
        Get a batch of jobs to execute.
        """

    async def __anext__(self) -> ScheduledJobBatch:
        try:
            return await self.get()
        except Completed:
            raise StopAsyncIteration from None

    def __aiter__(self) -> AsyncIterator[ScheduledJobBatch]:
        return self

    @abstractmethod
    async def cancel(self, reason: BaseException | None = None, /) -> None:
        """
        Close the scheduler and cancel any pending jobs.
        """

    @abstractmethod
    async def complete(self) -> None:
        """
        Close the scheduler and wait for any pending jobs to complete.
        """

    async def __aenter__(self) -> Self:
        await self.release()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_val is None:
            await self.complete()
        else:
            await self.cancel(exc_val)
