"""
Provide OS interaction utilities.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from asyncio import gather
from contextlib import suppress
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


async def link_or_copy(source_file_path: Path, destination_file_path: Path) -> None:
    """
    Create a hard link to a source path, or copy it to its destination otherwise.

    For most purposes, Betty requires files to be accessible at certain paths, rather than
    that these paths provide unique files. Therefore, the fastest thing to do is create
    hard links. In case that fails, such as when the source and destination are on different
    disks, copy the file instead. You **SHOULD NOT** use this function if the destination file
    will be modified afterwards.

    If the destination exists, it will be left untouched.
    """
    await asyncio.to_thread(_link_or_copy, source_file_path, destination_file_path)


def _link_or_copy(source_file_path: Path, destination_file_path: Path) -> None:
    try:
        _retry_link(source_file_path, destination_file_path)
    except OSError:
        _retry_copyfile(source_file_path, destination_file_path)


def _retry(
    f: Callable[[Path, Path], Any], source_file_path: Path, destination_file_path: Path
) -> None:
    try:
        f(source_file_path, destination_file_path)
    except FileNotFoundError:
        destination_file_path.parent.mkdir(parents=True, exist_ok=True)
        f(source_file_path, destination_file_path)


def _retry_link(source_file_path: Path, destination_file_path: Path) -> None:
    with suppress(FileExistsError):
        _retry(os.link, source_file_path, destination_file_path)


def _retry_copyfile(source_file_path: Path, destination_file_path: Path) -> None:
    with suppress(shutil.SameFileError):
        _retry(shutil.copyfile, source_file_path, destination_file_path)


async def copy_tree(
    source_directory_path: Path,
    destination_directory_path: Path,
    *,
    file_callback: Callable[[Path], Awaitable[Any]] | None = None,
) -> None:
    """
    Recursively copy all files in a source directory to a destination.
    """
    await gather(
        *(
            _copy_tree_file(
                source_directory_path / file_path,
                destination_directory_path / file_path,
                file_callback=file_callback,
            )
            for file_path in (
                Path(directory_path).relative_to(source_directory_path) / file_name
                for directory_path, _, file_names in walk(str(source_directory_path))
                for file_name in file_names
            )
        )
    )


async def _copy_tree_file(
    source_file_path: Path,
    destination_file_path: Path,
    *,
    file_callback: Callable[[Path], Awaitable[Any]] | None = None,
) -> None:
    await asyncio.to_thread(_retry_copyfile, source_file_path, destination_file_path)
    if file_callback:
        await file_callback(destination_file_path)
