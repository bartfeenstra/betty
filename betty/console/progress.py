"""
Output progress to the console.
"""

from typing import final

from rich.progress import Progress as RichProgress
from typing_extensions import override

from betty.concurrent import AsynchronizedLock
from betty.progress import Progress
from betty.typing import internal, threadsafe


@final
@internal
@threadsafe
class ConsoleProgress(Progress):
    """
    Output progress to Rich.
    """

    def __init__(self, rich_progress: RichProgress, rich_task_description: str):
        self._rich_progress = rich_progress
        self._rich_task = self._rich_progress.add_task(
            f"[green]{rich_task_description}", total=0
        )
        self._lock = AsynchronizedLock.new_threadsafe()
        self._total = 0

    @override
    async def add(self, add: int = 1) -> None:
        async with self._lock:
            self._total += add
            self._rich_progress.update(self._rich_task, total=self._total)

    @override
    async def done(self, done: int = 1) -> None:
        async with self._lock:
            self._rich_progress.update(self._rich_task, advance=done)
