import logging
import shutil
from contextlib import suppress
from enum import unique, IntFlag, auto

from betty import fs
from betty.locale import DEFAULT_LOCALIZER


@unique
class CacheScope(IntFlag):
    BETTY = auto()
    PROJECT = auto()


async def clear():
    with suppress(FileNotFoundError):
        shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
    logging.getLogger().info(DEFAULT_LOCALIZER._('All caches cleared.'))
