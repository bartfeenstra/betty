import hashlib
import os
import shutil
from collections import deque
from contextlib import suppress
from os import walk, path
from os.path import join, dirname, exists, relpath, getmtime
from shutil import copy2
from tempfile import mkdtemp
from typing import AsyncIterable


async def iterfiles(path: str) -> AsyncIterable[str]:
    for dir_path, _, filenames in walk(path):
        for filename in filenames:
            yield join(dir_path, filename)


def makedirs(path: str) -> None:
    os.makedirs(path, 0o755, True)


def hashfile(path: str) -> str:
    return hashlib.md5(':'.join([str(getmtime(path)), path]).encode('utf-8')).hexdigest()


class FileSystem:
    def __init__(self, *paths):
        self._paths = deque(paths)

    @property
    def paths(self) -> deque:
        return self._paths

    async def open(self, *file_paths: str):
        for file_path in file_paths:
            for fs_path in self._paths:
                with suppress(FileNotFoundError):
                    return open(join(fs_path, file_path))
        raise FileNotFoundError

    async def copy2(self, source_path: str, destination_path: str) -> str:
        for fs_path in self._paths:
            with suppress(FileNotFoundError):
                return copy2(join(fs_path, source_path), destination_path)
        tried_paths = [join(fs_path, source_path) for fs_path in self._paths]
        raise FileNotFoundError('Could not find any of %s.' %
                                ', '.join(tried_paths))

    async def copytree(self, source_path: str, destination_path: str) -> str:
        for fs_path in self._paths:
            async for file_source_path in iterfiles(join(fs_path, source_path)):
                file_destination_path = join(destination_path, relpath(
                    file_source_path, join(fs_path, source_path)))
                if not exists(file_destination_path):
                    makedirs(dirname(file_destination_path))
                    copy2(file_source_path, file_destination_path)
        return destination_path


class DirectoryBackup:
    def __init__(self, root_path: str, backup_path: str):
        self._root_path = root_path
        self._backup_path = backup_path

    async def __aenter__(self):
        self._tmp = mkdtemp()
        with suppress(FileNotFoundError):
            shutil.move(path.join(self._root_path, self._backup_path), self._tmp)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with suppress(FileNotFoundError):
            shutil.move(path.join(self._tmp, self._backup_path),
                        path.join(self._root_path, self._backup_path))
        shutil.rmtree(self._tmp)
