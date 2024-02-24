"""
Provide utilities for running jobs concurrently.
"""

from __future__ import annotations

import threading


class Context:
    def __init__(self):
        self._claims_lock = threading.Lock()
        self._claimed_job_ids: set[str] = set()

    def claim(self, job_id: str) -> bool:
        with self._claims_lock:
            if job_id in self._claimed_job_ids:
                return False
            self._claimed_job_ids.add(job_id)
        return True
