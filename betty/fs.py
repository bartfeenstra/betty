import hashlib
import os
from collections import deque
from contextlib import suppress
from os.path import getmtime
from pathlib import Path
from shutil import copy2
from typing import AsyncIterable, Optional, Tuple, AsyncContextManager, Sequence

import aiofiles

from betty import _ROOT_DIRECTORY_PATH
from betty.os import PathLike


ROOT_DIRECTORY_PATH = _ROOT_DIRECTORY_PATH


ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / 'betty' / 'assets'


CACHE_DIRECTORY_PATH = Path.home() / '.betty'


async def iterfiles(path: PathLike) -> AsyncIterable[Path]:
    for dir_path, _, filenames in os.walk(path):
        for filename in filenames:
            yield Path(dir_path) / filename


def hashfile(path: PathLike) -> str:
    return hashlib.md5(':'.join([str(getmtime(path)), str(path)]).encode('utf-8')).hexdigest()


class FileSystem:
    class _Open:
        def __init__(self, fs: 'FileSystem', file_paths: Tuple[PathLike]):
            self._fs = fs
            self._file_paths = file_paths
            self._file = None

        async def __aenter__(self):
            for file_path in map(Path, self._file_paths):
                for fs_path, fs_encoding in self._fs._paths:
                    with suppress(FileNotFoundError):
                        self._file = aiofiles.open(fs_path / file_path, encoding=fs_encoding)
                        return await self._file.__aenter__()
            raise FileNotFoundError

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self._file is not None:
                await self._file.__aexit__(None, None, None)

    def __init__(self, *paths: Tuple[PathLike, Optional[str]]):
        self._paths = deque([(Path(fs_path), fs_encoding) for fs_path, fs_encoding in paths])

    def __len__(self) -> int:
        return len(self._paths)

    @property
    def paths(self) -> Sequence[Tuple[Path, str]]:
        return list(self._paths)

    def prepend(self, path: PathLike, fs_encoding: Optional[str] = None) -> None:
        self._paths.appendleft((Path(path), fs_encoding))

    def clear(self) -> None:
        self._paths.clear()

    def open(self, *file_paths: PathLike) -> AsyncContextManager[object]:
        return self._Open(self, file_paths)

    async def copy2(self, source_path: PathLike, destination_path: PathLike) -> Path:
        for fs_path, _ in self._paths:
            with suppress(FileNotFoundError):
                return copy2(fs_path / source_path, destination_path)
        tried_paths = [str(fs_path / source_path) for fs_path, _ in self._paths]
        raise FileNotFoundError('Could not find any of %s.' % ', '.join(tried_paths))

    async def copytree(self, source_path: PathLike, destination_path: PathLike) -> Path:
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        for fs_path, _ in self._paths:
            async for file_source_path in iterfiles(fs_path / source_path):
                file_destination_path = destination_path / file_source_path.relative_to(fs_path / source_path)
                if not file_destination_path.exists():
                    file_destination_path.parent.mkdir(exist_ok=True, parents=True)
                    copy2(file_source_path, file_destination_path)
        return destination_path
