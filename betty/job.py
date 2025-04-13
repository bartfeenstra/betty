"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from betty.cache.memory import MemoryCache
from betty.concurrent import ensure_manager

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager

    from betty.cache import Cache


class Context:
    """
    Define a job context.
    """

    def __init__(self, *, manager: SyncManager | None = None):
        manager = ensure_manager(manager)
        self._id = str(uuid4())
        self._cache: Cache[Any] = MemoryCache(manager=manager)
        self._start = datetime.now()

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
