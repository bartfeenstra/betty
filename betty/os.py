import os
import shutil
from typing import Union

PathLike = Union[str, os.PathLike]


def link_or_copy(source_path: PathLike, destination_path: PathLike) -> None:
    try:
        os.link(source_path, destination_path)
    except OSError:
        shutil.copyfile(source_path, destination_path)


class ChDir:
    def __init__(self, directory_path: PathLike):
        self._directory_path = directory_path
        self._owd = None

    def __enter__(self) -> None:
        self.change()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.revert()

    def change(self) -> 'ChDir':
        self._owd = os.getcwd()
        os.chdir(self._directory_path)
        return self

    def revert(self) -> None:
        os.chdir(self._owd)
