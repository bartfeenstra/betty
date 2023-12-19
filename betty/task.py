from __future__ import annotations

import multiprocessing
from collections.abc import MutableSequence


class Context:
    def __init__(self):
        self._claims_lock = multiprocessing.Manager().Lock()
        self._claimed_task_ids: MutableSequence[str] = multiprocessing.Manager().list()

    def claim(self, task_id: str) -> bool:
        with self._claims_lock:
            if task_id in self._claimed_task_ids:
                return False
            self._claimed_task_ids.append(task_id)
            return True
