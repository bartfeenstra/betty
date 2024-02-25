"""
Provide the Cache API.
"""
import asyncio
import logging
import shutil
from contextlib import suppress
from pathlib import Path

from betty.locale import Localizer


class _Cache:
    async def clear(self) -> None:
        raise NotImplementedError


class FileCache(_Cache):
    def __init__(
        self,
        localizer: Localizer,
        cache_directory_path: Path,
        /,
    ):
        self._localizer = localizer
        self._path = cache_directory_path

    @property
    def path(self) -> Path:
        return self._path

    async def clear(self) -> None:
        with suppress(FileNotFoundError):
            await asyncio.to_thread(shutil.rmtree, self.path)
        logging.getLogger(__name__).info(self._localizer._('All caches cleared.'))
