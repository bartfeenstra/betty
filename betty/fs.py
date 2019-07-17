import hashlib
import os
from collections import deque
from os import walk
from os.path import join, dirname, exists, relpath
from shutil import copy2
from typing import Iterable


def iterfiles(path: str) -> Iterable[str]:
    return [join(dir_path, filename) for dir_path, _, filenames in walk(path) for filename in filenames]


def makedirs(path: str) -> None:
    os.makedirs(path, 0o755, True)


BLOCK_SIZE = 65536


def hashfile(path: str) -> str:
    hasher = hashlib.md5()
    with open(path, 'rb') as file:
        while True:
            buffer = file.read(BLOCK_SIZE)
            if len(buffer) == 0:
                break
            hasher.update(buffer)
    return hasher.hexdigest()


class FileSystem:
    def __init__(self, *paths):
        self._paths = deque(paths)

    @property
    def paths(self) -> deque:
        return self._paths

    def open(self, *file_paths: str):
        for file_path in file_paths:
            for fs_path in self._paths:
                try:
                    return open(join(fs_path, file_path))
                except FileNotFoundError:
                    pass
        raise FileNotFoundError

    def copy2(self, source_path: str, destination_path: str) -> str:
        for fs_path in self._paths:
            try:
                return copy2(join(fs_path, source_path), destination_path)
            except FileNotFoundError:
                pass
        tried_paths = [join(fs_path, source_path) for fs_path in self._paths]
        raise FileNotFoundError('Could not find any of %s.' %
                                ', '.join(tried_paths))

    def copytree(self, source_path: str, destination_path: str) -> str:
        for fs_path in self._paths:
            for file_source_path in iterfiles(join(fs_path, source_path)):
                file_destination_path = join(destination_path, relpath(
                    file_source_path, join(fs_path, source_path)))
                if not exists(file_destination_path):
                    makedirs(dirname(file_destination_path))
                    copy2(file_source_path, file_destination_path)
        return destination_path
