import hashlib
import os
import shutil
from collections import deque
from contextlib import suppress
from os.path import getmtime
from pathlib import Path
from shutil import copy2
from tempfile import mkdtemp
from typing import AsyncIterable, Optional, Tuple

from betty.os import PathLike

ROOT_DIRECTORY_PATH = Path(__file__).resolve().parents[1]


CACHE_DIRECTORY_PATH = Path.home() / '.betty'


async def iterfiles(path: PathLike) -> AsyncIterable[Path]:
    for dir_path, _, filenames in os.walk(path):
        for filename in filenames:
            yield Path(dir_path) / filename


def hashfile(path: PathLike) -> str:
    return hashlib.md5(':'.join([str(getmtime(path)), str(path)]).encode('utf-8')).hexdigest()


class FileSystem:
    def __init__(self, *paths: Tuple[PathLike, Optional[str]]):
        self._paths = deque([(Path(fs_path), fs_encoding) for fs_path, fs_encoding in paths])

    @property
    def paths(self) -> deque:
        return self._paths

    async def open(self, *file_paths: PathLike):
        for file_path in map(Path, file_paths):
            for fs_path, fs_encoding in self._paths:
                with suppress(FileNotFoundError):
                    return open(fs_path / file_path, encoding=fs_encoding)
        raise FileNotFoundError

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


class DirectoryBackup:
    def __init__(self, root_path: PathLike, backup_path: PathLike):
        self._root_path = Path(root_path)
        self._backup_path = Path(backup_path)

    async def __aenter__(self):
        self._tmp = mkdtemp()
        with suppress(FileNotFoundError):
            shutil.move(str(self._root_path / self._backup_path), self._tmp)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with suppress(FileNotFoundError):
            shutil.move(str(self._tmp / self._backup_path), str(self._root_path / self._backup_path))
        shutil.rmtree(self._tmp)
