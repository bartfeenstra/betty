"""
Provide the Cache API.
"""
import asyncio
import logging
import shutil
from contextlib import suppress

from betty import fs
from betty.locale import Localizer


class Cache:
    def __init__(self, localizer: Localizer):
        self._localizer = localizer

    async def clear(self) -> None:
        with suppress(FileNotFoundError):
            await asyncio.to_thread(shutil.rmtree, fs.CACHE_DIRECTORY_PATH)
        logging.getLogger(__name__).info(self._localizer._('All caches cleared.'))
