import logging
import shutil
from contextlib import suppress
from enum import unique, IntFlag, auto

from betty import fs
from betty.locale import Localizer


@unique
class CacheScope(IntFlag):
    BETTY = auto()
    PROJECT = auto()


class Cache:
    def __init__(self, localizer: Localizer):
        self._localizer = localizer

    async def clear(self) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
        logging.getLogger().info(self._localizer._('All caches cleared.'))
