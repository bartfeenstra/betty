"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, final
from uuid import uuid4

from betty.progresses.no_op import NoOpProgress
from betty.stores.memory import MemoryStore

if TYPE_CHECKING:
    from collections.abc import Iterable, Set

    from betty.job.scheduler import Scheduler
    from betty.progress import Progress
    from betty.store import Store


@final
class Context:
    """
    A job context.
    """

    def __init__(self, *, progress: Progress | None = None):
        self.id: Final[str] = str(uuid4())
        """
        The unique job context ID.
        """
        self.store: Final[Store[Any]] = MemoryStore()
        """
        The key-value store for this job context.

        The store is guaranteed to be additive only, never deleting items, until the job context is done. 
        """
        self.start: Final[datetime] = datetime.now(tz=UTC)
        """
        When the job started.
        """
        self.progress: Final[Progress] = progress or NoOpProgress()
        """
        The job progress.
        """


class Job(ABC):
    """
    A job.
    """

    def __init__(
        self,
        job_id: str,
        *,
        dependencies: Iterable[str] = (),
        dependents: Iterable[str] = (),
        priority: bool = False,
    ):
        self.id: Final[str] = job_id
        """
        The unique job ID.
        """
        self.dependencies: Final[Set[str]] = set(dependencies)
        """
        The IDs of any other jobs this job depends on.
        """
        self.dependents: Final[Set[str]] = set(dependents)
        """
        The IDs of any other jobs that depend on this job.
        """
        self.priority: Final[bool] = priority
        """
        Whether the job has priority over others.
        """

    @abstractmethod
    async def do(self, scheduler: Scheduler, /) -> None:
        """
        Do the job.
        """
