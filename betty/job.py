"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, TYPE_CHECKING

from betty.cache.memory import MemoryCache
from betty.locale import Localizer, DEFAULT_LOCALIZER

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
