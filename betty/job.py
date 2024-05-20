"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

import threading
from typing import Any, TYPE_CHECKING

from betty.cache.memory import MemoryCache
from betty.locale import Localizer, DEFAULT_LOCALIZER
from betty.warnings import deprecated

if TYPE_CHECKING:
    from betty.cache import Cache


class Context:
    """
    Define a job context.
    """

    def __init__(self, localizer: Localizer | None = None):
        self._cache: Cache[Any] = MemoryCache(localizer or DEFAULT_LOCALIZER)
        self._claims_lock = threading.Lock()
        self._claimed_job_ids: set[str] = set()

    @deprecated(
        "This method is deprecated as of Betty 0.3.3, and will be removed in Betty 0.4.x. Use `Context.cache` instead."
    )
    def claim(self, job_id: str) -> bool:
        """
        Claim a job within this context.
        """
        with self._claims_lock:
            if job_id in self._claimed_job_ids:
                return False
            self._claimed_job_ids.add(job_id)
        return True

    @property
    def cache(self) -> Cache[Any]:
        """
        Provide a cache for this job context.

        The cache is volatile and will be discarded once the job context is completed.
        """
        return self._cache
