"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from betty.cache.memory import MemoryCache

if TYPE_CHECKING:
    from betty.cache import Cache


class Context:
    """
    Define a job context.
    """

    def __init__(self):
        self._cache: Cache[Any] = MemoryCache()
        self._start = datetime.now()

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
