"""
Provide OS interaction utilities.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.pathlib import StrPath, resolve_path
from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Callable


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


class FileNotFound(Invalid, FileNotFoundError):
    """
    Raised when a file cannot be found.
    """

    def __init__(self, file: StrPath, /):
        super().__init__(
            _("Could not find the file {file_path}.").format(file_path=Quote(str(file)))
        )
