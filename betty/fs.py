"""
Provide file system utilities.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from collections import deque
from contextlib import suppress
from pathlib import Path
from shutil import copy2
from typing import AsyncIterable, AsyncContextManager, Sequence, TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

from betty import _ROOT_DIRECTORY_PATH
from betty.warnings import deprecated

if TYPE_CHECKING:
    from aiofiles.threadpool.text import AsyncTextIOWrapper
    from types import TracebackType

ROOT_DIRECTORY_PATH = _ROOT_DIRECTORY_PATH


ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "betty" / "assets"


PREBUILT_ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "prebuild"


HOME_DIRECTORY_PATH = Path.home() / ".betty"


async def iterfiles(path: Path) -> AsyncIterable[Path]:
    """
    Recursively iterate over any files found in a directory.
    """
    for dir_path, _, filenames in os.walk(str(path)):
        for filename in filenames:
            yield Path(dir_path) / filename


@deprecated(
    "This function is deprecated as of Betty 0.3.4, and will be removed in Betty 0.4.x. Instead, use `betty.hashid.hashid_file_meta()`."
)
def hashfile(path: Path) -> str:
    """
    Get a hash for a file.

    This function relies on the file path and last modified time for uniqueness.
    File contents are ignored.
    """
    return hashlib.md5(f"{path.stat().st_mtime}:{path}".encode("utf-8")).hexdigest()


class _Open:
    def __init__(self, fs: FileSystem, file_paths: tuple[Path, ...]):
        self._fs = fs
        self._file_paths = file_paths
        self._file: AsyncContextManager[AsyncTextIOWrapper] | None = None

    async def __aenter__(self) -> AsyncTextIOWrapper:
        for file_path in map(Path, self._file_paths):
            for fs_path, fs_encoding in self._fs._paths:
                with suppress(FileNotFoundError):
                    self._file = aiofiles.open(
                        fs_path / file_path, encoding=fs_encoding
                    )
                    return await self._file.__aenter__()
        raise FileNotFoundError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._file is not None:
            await self._file.__aexit__(None, None, None)


class FileSystem:
    """
    A layered file system.

    A file system unifies several directory paths on disk, overlaying them on
    each other. Paths added later act as fallbacks, e.g. earlier paths have priority.
    """

    def __init__(self, *paths: tuple[Path, str | None]):
        self._paths = deque(paths)

    def __len__(self) -> int:
        return len(self._paths)

    @property
    def paths(self) -> Sequence[tuple[Path, str | None]]:
        """
        The paths to the individual layers.
        """
        return list(self._paths)

    def prepend(self, path: Path, fs_encoding: str | None = None) -> None:
        """
        Prepend a layer path, e.g. override existing layers with the given one.
        """
        self._paths.appendleft((path, fs_encoding))

    def clear(self) -> None:
        """
        Clear all layers from the file system.
        """
        self._paths.clear()

    def open(self, *file_paths: Path) -> _Open:
        """
        Open a file.

        :param file_paths: One or more file paths within the file system. The first file path to exist
        will cause this function to return. Previously missing file paths will not cause errors.

        :raise FileNotFoundError: Raised when none of the provided paths matches an existing file.
        """
        return _Open(self, file_paths)

    async def copy2(self, source_path: Path, destination_path: Path) -> Path:
        """
        Copy a file to a destination using :py:func:`shutil.copy2`.
        """
        for fs_path, _ in self._paths:
            with suppress(FileNotFoundError):
                await asyncio.to_thread(copy2, fs_path / source_path, destination_path)
                return destination_path
        tried_paths = [str(fs_path / source_path) for fs_path, _ in self._paths]
        raise FileNotFoundError("Could not find any of %s." % ", ".join(tried_paths))

    async def copytree(
        self, source_path: Path, destination_path: Path
    ) -> AsyncIterable[Path]:
        """
        Recursively copy the files in a directory tree to another directory.
        """
        file_destination_paths = set()
        for fs_path, _ in self._paths:
            async for file_source_path in iterfiles(fs_path / source_path):
                file_destination_path = destination_path / file_source_path.relative_to(
                    fs_path / source_path
                )
                if file_destination_path not in file_destination_paths:
                    file_destination_paths.add(file_destination_path)
                    await makedirs(file_destination_path.parent, exist_ok=True)
                    await asyncio.to_thread(
                        copy2, file_source_path, file_destination_path
                    )
                    yield file_destination_path
