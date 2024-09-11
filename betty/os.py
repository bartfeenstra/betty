"""
Provide OS interaction utilities.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Awaitable
from contextlib import suppress
from os import walk
from pathlib import Path
from typing import Any, TypeAlias

from betty.asyncio import gather, make_async

CopyFunction: TypeAlias = Callable[[Path, Path], Awaitable[Path]]


DEFAULT_COPY_FUNCTION: CopyFunction = make_async(shutil.copyfile)


async def link_or_copy(
    source_file_path: Path,
    destination_file_path: Path,
    *,
    copy_function: CopyFunction = DEFAULT_COPY_FUNCTION,
) -> None:
    """
    Create a hard link to a source path, or copy it to its destination otherwise.

    For most purposes, Betty requires files to be accessible at certain paths, rather than
    that these paths provide unique files. Therefore, the fastest thing to do is create
    hard links. In case that fails, such as when the source and destination are on different
    disks, copy the file instead. You **SHOULD NOT** use this function if the destination file
    will be modified afterwards.

    If the destination exists, it will be left untouched.
    """
    try:
        await _retry_link(source_file_path, destination_file_path)
    except OSError:
        await _retry_copy(
            source_file_path, destination_file_path, copy_function=copy_function
        )


async def _retry(
    f: Callable[[Path, Path], Awaitable[Any]],
    source_file_path: Path,
    destination_file_path: Path,
) -> None:
    try:
        await f(source_file_path, destination_file_path)
    except FileNotFoundError:
        destination_file_path.parent.mkdir(parents=True, exist_ok=True)
        await f(source_file_path, destination_file_path)


async def _retry_link(source_file_path: Path, destination_file_path: Path) -> None:
    with suppress(FileExistsError):
        await _retry(make_async(os.link), source_file_path, destination_file_path)


async def _retry_copy(
    source_file_path: Path,
    destination_file_path: Path,
    *,
    copy_function: CopyFunction,
) -> None:
    with suppress(shutil.SameFileError):
        await _retry(copy_function, source_file_path, destination_file_path)


async def copy_tree(
    source_directory_path: Path,
    destination_directory_path: Path,
    *,
    copy_function: CopyFunction = DEFAULT_COPY_FUNCTION,
) -> None:
    """
    Recursively copy all files in a source directory to a destination.
    """
    await gather(
        *(
            _retry_copy(
                source_directory_path / file_path,
                destination_directory_path / file_path,
                copy_function=copy_function,
            )
            for file_path in (
                Path(directory_path).relative_to(source_directory_path) / file_name
                for directory_path, _, file_names in walk(str(source_directory_path))
                for file_name in file_names
            )
        )
    )
