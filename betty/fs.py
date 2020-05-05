import hashlib
import os
import shutil
from collections import deque
from contextlib import suppress
from os import walk, path
from os.path import join, dirname, exists, relpath, getmtime
from shutil import copy
from tempfile import mkdtemp, TemporaryDirectory
from typing import AsyncIterable


async def iterfiles(path: str) -> AsyncIterable[str]:
    for dir_path, _, filenames in walk(path):
        for filename in filenames:
            yield join(dir_path, filename)


def makedirs(path: str) -> None:
    os.makedirs(path, 0o755, True)


def hashfile(path: str) -> str:
    return hashlib.md5(':'.join([str(getmtime(path)), path]).encode('utf-8')).hexdigest()


async def _copytree(source_path: str, destination_path: str):
    async for file_source_path in iterfiles(source_path):
        file_destination_path = join(destination_path, relpath(file_source_path, source_path))
        if not exists(file_destination_path):
            makedirs(dirname(file_destination_path))
            copy(file_source_path, file_destination_path)


class CopyTreeTo:
    def __init__(self, file_system: 'FileSystem', source_path: str):
        self._file_system = file_system
        self._source_path = source_path

    async def __aenter__(self):
        self._intermediate_directory = TemporaryDirectory()
        await self._file_system.copy_tree(self._source_path, self._intermediate_directory.name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._intermediate_directory.cleanup()

    async def copy_to(self, destination_path: str) -> None:
        await _copytree(self._intermediate_directory.name, destination_path)


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

    async def copy(self, source_path: str, destination_path: str) -> str:
        for fs_path in self._paths:
            with suppress(FileNotFoundError):
                return copy(join(fs_path, source_path), destination_path)
        tried_paths = [join(fs_path, source_path) for fs_path in self._paths]
        raise FileNotFoundError('Could not find any of %s.' %
                                ', '.join(tried_paths))

    async def copy_tree(self, source_path: str, destination_path: str) -> str:
        makedirs(destination_path)
        for fs_path in self._paths:
            await _copytree(join(fs_path, source_path), destination_path)
        return destination_path

    def copy_tree_to(self, source_path: str) -> CopyTreeTo:
        return CopyTreeTo(self, source_path)


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
