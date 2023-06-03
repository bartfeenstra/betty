import logging
import shutil
from contextlib import suppress
from enum import unique, IntFlag, auto

from betty import fs
from betty.locale import Localizable


@unique
class CacheScope(IntFlag):
    BETTY = auto()
    PROJECT = auto()


class Cache(Localizable):
    async def clear(self) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
        logging.getLogger().info(self.localizer._('All caches cleared.'))
