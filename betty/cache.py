import logging
import shutil
import threading
from contextlib import suppress
from typing import TYPE_CHECKING, Iterator, Optional

from betty import fs

if TYPE_CHECKING:
    from betty.builtins import _


async def clear():
    with suppress(FileNotFoundError):
        shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
    logging.getLogger().info(_('All caches cleared.'))


class TaskCache:
    def __init__(self):
        self._tasks = set()

    @property
    def tasks(self) -> Iterator[str]:
        yield from self._tasks

    def claim(self, task: str) -> bool:
        if task in self._tasks:
            return False
        self._tasks.add(task)
        return True

    def __contains__(self, item) -> bool:
        with threading.Lock():
            return item in self._tasks


class IOTaskCache(TaskCache):
    def __enter__(self):
        global io_task_cache

        if io_task_cache is not _default_io_task_cache:
            raise RuntimeError('Another cache is already active.')
        io_task_cache = self

    def __exit__(self, __, ___, ____):
        global io_task_cache

        io_task_cache = _default_io_task_cache


class AlwaysClaimTaskCache(TaskCache):
    def claim(self, task: str) -> bool:
        return True


_default_io_task_cache: TaskCache = AlwaysClaimTaskCache()
io_task_cache: TaskCache = _default_io_task_cache
