"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, final
from uuid import uuid4

from betty.cache.memory import MemoryCache
from betty.progress.no_op import NoOpProgress

if TYPE_CHECKING:
    from betty.cache import Cache
    from betty.job.scheduler import Scheduler
    from betty.progress import Progress


@final
class Context:
    """
    A job context.
    """

    def __init__(self, *, progress: Progress | None = None):
        self._id = str(uuid4())
        self._cache = MemoryCache()
        self._start = datetime.now(tz=UTC)
        self._progress = progress or NoOpProgress()

    @property
    def id(self) -> str:
        """
        The unique job context ID.
        """
        return self._id

    @property
    def cache(self) -> Cache[Any]:
        """
        Provide a cache for this job context.

        The cache is volatile and will be discarded once the job context is completed.
        """
        return self._cache

    @property
    def start(self) -> datetime:
        """
        When the job started.
        """
        return self._start

    @property
    def progress(self) -> Progress:
        """
        The job progress.
        """
        return self._progress


class Job(ABC):
    """
    A job.
    """

    def __init__(
        self,
        job_id: str,
        *,
        dependencies: set[str] | None = None,
        dependents: set[str] | None = None,
        priority: bool = False,
    ):
        self._called = False
        self._id = job_id
        self._dependencies = set() if dependencies is None else dependencies
        self._dependents = set() if dependents is None else dependents
        self._priority = priority

    @property
    def id(self) -> str:
        """
        The unique job ID.
        """
        return self._id

    @property
    def dependencies(self) -> set[str]:
        """
        The IDs of any other jobs this job depends on.
        """
        return self._dependencies

    @property
    def dependents(self) -> set[str]:
        """
        The IDs of any other jobs that depend on this job.
        """
        return self._dependents

    @property
    def priority(self) -> bool:
        """
        Whether the job has priority over others.
        """
        return self._priority

    @abstractmethod
    async def do(self, scheduler: Scheduler, /) -> None:
        """
        Do the job.
        """
