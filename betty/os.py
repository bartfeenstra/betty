"""
Provide OS interaction utilities.
"""
from __future__ import annotations

import asyncio
import os
import shutil
from contextlib import suppress
from pathlib import Path
from types import TracebackType

from aiofiles.os import link, makedirs


async def link_or_copy(source_path: Path, destination_path: Path) -> None:
    """
    Create a symlink to a source path, or copy it to its destination otherwise.

    For most purposes, Betty requires files to be accessible at certain paths, rather than
    that these paths provide unique files. Therefore, the fastest thing to do is create
    symlinks. In case that fails, such as when the source and destination are on different
    disks, copy the file instead.
    """
    try:
        with suppress(FileExistsError):
            await link(source_path, destination_path)
    except OSError:
        with suppress(shutil.SameFileError):
            await asyncio.to_thread(shutil.copyfile, source_path, destination_path)


class ChDir:
    def __init__(self, directory_path: Path):
        self._directory_path = directory_path
        self._owd: str | None = None

    async def __aenter__(self) -> None:
        await self.change()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        await self.revert()

    async def change(self) -> None:
        self._owd = os.getcwd()
        await makedirs(self._directory_path, exist_ok=True)
        os.chdir(self._directory_path)

    async def revert(self) -> None:
        owd = self._owd
        if owd is not None:
            os.chdir(owd)
