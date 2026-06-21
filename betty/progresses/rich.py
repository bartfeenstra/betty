"""
Output progress to Rich.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.concurrent import ThreadSafeLock
from betty.progress import Progress
from betty.typing import threadsafe

if TYPE_CHECKING:
    from rich.progress import Progress as _RichProgress


@final
@threadsafe
class RichProgress(Progress):
    """
    Output progress to Rich.
    """

    def __init__(self, rich_progress: _RichProgress, rich_task_description: str):
        self._rich_progress = rich_progress
        self._rich_task = self._rich_progress.add_task(
            f"[green]{rich_task_description}", total=0
        )
        self._lock = ThreadSafeLock()
        self._total = 0

    @override
    async def add(self, add: int = 1, /) -> None:
        async with self._lock:
            self._total += add
            self._rich_progress.update(self._rich_task, total=self._total)

    @override
    async def done(self, done: int = 1, /) -> None:
        async with self._lock:
            self._rich_progress.update(self._rich_task, advance=done)
