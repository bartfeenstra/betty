import os
import shutil
from pathlib import Path
from typing import Optional, TypeVar

PathLike = TypeVar('PathLike', str, os.PathLike[str])


def link_or_copy(source_path: PathLike, destination_path: PathLike) -> None:
    try:
        os.link(source_path, destination_path)
    except OSError:
        shutil.copyfile(Path(source_path), Path(destination_path))


class ChDir:
    def __init__(self, directory_path: PathLike):
        self._directory_path = directory_path
        self._owd: Optional[str] = None

    def __enter__(self) -> None:
        self.change()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.revert()

    def change(self) -> 'ChDir':
        self._owd = os.getcwd()
        os.chdir(self._directory_path)
        return self

    def revert(self) -> None:
        if self._owd is None:
            return
        os.chdir(self._owd)
