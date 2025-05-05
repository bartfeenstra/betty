"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from betty.cache.memory import MemoryCache
from betty.test_utils.progress import NoOpProgress

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager

    from betty.cache import Cache
    from betty.progress import Progress


class Context:
    """
    Define a job context.
    """

    def __init__(self, *, manager: SyncManager, progress: Progress | None = None):
        self._id = str(uuid4())
        self._cache: Cache[Any] = MemoryCache(manager=manager)
        self._start = datetime.now()
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
