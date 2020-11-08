import hashlib
import os
import shutil
from collections import deque
from contextlib import suppress
from os import walk, path
from tempfile import mkdtemp, TemporaryDirectory
from typing import Iterable


def iterfiles(file_path: str) -> Iterable[str]:
    for dir_path, _, filenames in walk(file_path):
        for filename in filenames:
            yield path.join(dir_path, filename)


def makedirs(file_path: str) -> None:
    os.makedirs(file_path, 0o755, True)


def hashfile(file_path: str) -> str:
    return hashlib.md5(':'.join([str(path.getmtime(file_path)), file_path]).encode('utf-8')).hexdigest()


async def copy_tree(source_path: str, destination_path: str):
    for file_source_path in iterfiles(source_path):
        file_destination_path = path.join(destination_path, path.relpath(file_source_path, source_path))
        try:
            shutil.copy2(file_source_path, file_destination_path)
        except FileNotFoundError:
            makedirs(path.dirname(file_destination_path))
            shutil.copy2(file_source_path, file_destination_path)


class CopyTreeTo:
    def __init__(self, file_system: 'FileSystem', source_path: str):
        self._file_system = file_system
        self._source_path = source_path

    async def __aenter__(self) -> 'CopyTreeTo':
        self._intermediate_directory = TemporaryDirectory()
        await self._file_system.copy_tree(self._source_path, self._intermediate_directory.name)
        return self

    async def __call__(self, destination_path: str) -> None:
        await copy_tree(self._intermediate_directory.name, destination_path)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._intermediate_directory.cleanup()


class FileSystem:
    def __init__(self, *paths: str):
        """
        :param paths: The paths to each individual layer of the file system, from high to low priority.
        """
        self._paths = deque(paths)

    @property
    def paths(self) -> deque:
        return self._paths

    async def copy(self, source_path: str, destination_path: str) -> None:
        makedirs(path.dirname(destination_path))

        for fs_path in self._paths:
            with suppress(FileNotFoundError):
                return shutil.copyfile(path.join(fs_path, source_path), destination_path)

        tried_paths = [path. join(fs_path, source_path) for fs_path in self._paths]
        raise FileNotFoundError('Could not find any of %s.' % ', '.join(tried_paths))

    async def copy_tree(self, source_path: str, destination_path: str) -> None:
        makedirs(destination_path)

        tries = []
        for fs_path in reversed(self._paths):
            try:
                await copy_tree(path.join(fs_path, source_path), destination_path)
                tries.append(True)
            except FileNotFoundError:
                tries.append(False)

        if True not in tries:
            tried_paths = [path. join(fs_path, source_path) for fs_path in self._paths]
            raise FileNotFoundError('Could not find any of %s.' % ', '.join(tried_paths))

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
