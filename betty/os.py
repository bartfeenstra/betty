"""
Provide OS interaction utilities.
"""

from __future__ import annotations

import asyncio
import shutil
from contextlib import suppress

from aiofiles.os import link
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


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
