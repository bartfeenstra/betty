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


def copy_tree(source_path: str, destination_path: str):
    makedirs(destination_path)
    for file_source_path in iterfiles(source_path):
        file_destination_path = path.join(destination_path, path.relpath(file_source_path, source_path))
        try:
            shutil.copy(file_source_path, file_destination_path)
        except FileNotFoundError:
            makedirs(path.dirname(file_destination_path))
            shutil.copy(file_source_path, file_destination_path)


class CopyTreeTo:
    def __init__(self, file_system: 'FileSystem', source_path: str):
        self._file_system = file_system
        self._source_path = source_path

    def __enter__(self) -> 'CopyTreeTo':
        self._intermediate_directory = TemporaryDirectory()
        self._file_system.copy_tree(self._source_path, self._intermediate_directory.name)
        return self

    def __call__(self, destination_path: str) -> None:
        copy_tree(self._intermediate_directory.name, destination_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._intermediate_directory.cleanup()


class FileSystem:
    def __init__(self, *paths):
        self._paths = deque(paths)

    @property
    def paths(self) -> deque:
        return self._paths

    def copy(self, source_path: str, destination_path: str) -> None:
        for fs_path in self._paths:
            with suppress(FileNotFoundError):
                shutil.copyfile(path.join(fs_path, source_path), destination_path)

    def copy_tree(self, source_path: str, destination_path: str) -> None:
        for fs_path in self._paths:
            with suppress(FileNotFoundError):
                copy_tree(path.join(fs_path, source_path), destination_path)

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
