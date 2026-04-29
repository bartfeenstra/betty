"""
Provide OS interaction utilities.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from betty.pathlib import resolve_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.pathlib import StrPath


async def link_or_copy(source_file: StrPath, destination_file: StrPath, /) -> None:
    """
    Create a hard link to a source path, or copy it to its destination otherwise.

    For most purposes, Betty requires files to be accessible at certain paths, rather than
    that these paths provide unique files. Therefore, the fastest thing to do is create
    hard links. In case that fails, such as when the source and destination are on different
    disks, copy the file instead. You **SHOULD NOT** use this function if the destination file
    will be modified afterwards.

    If the destination exists, it will be left untouched.
    """
    await asyncio.to_thread(_link_or_copy, source_file, destination_file)


def _link_or_copy(source_file: StrPath, destination_file: StrPath, /) -> None:
    try:
        _retry_link(source_file, destination_file)
    except OSError:
        _retry_copyfile(source_file, destination_file)


def _retry(
    f: Callable[[StrPath, StrPath], Any],
    source_file: StrPath,
    destination_file: StrPath,
) -> None:
    try:
        f(source_file, destination_file)
    except FileNotFoundError:
        resolve_path(destination_file).parent.mkdir(exist_ok=True, parents=True)
        f(source_file, destination_file)


def _retry_link(source_file: StrPath, destination_file: StrPath) -> None:
    with suppress(FileExistsError):
        _retry(os.link, source_file, destination_file)


def _retry_copyfile(source_file: StrPath, destination_file: StrPath) -> None:
    with suppress(shutil.SameFileError):
        _retry(shutil.copyfile, source_file, destination_file)
