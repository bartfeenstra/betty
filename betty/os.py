from __future__ import annotations

import os
import shutil
from contextlib import suppress
from pathlib import Path
from types import TracebackType


def link_or_copy(source_path: Path, destination_path: Path) -> None:
    try:
        with suppress(FileExistsError):
            os.link(source_path, destination_path)
    except OSError:
        with suppress(shutil.SameFileError):
            shutil.copyfile(source_path, destination_path)


class ChDir:
    def __init__(self, directory_path: Path):
        self._directory_path = directory_path
        self._owd: str | None = None

    def __enter__(self) -> None:
        self.change()

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        self.revert()

    def change(self) -> None:
        self._owd = os.getcwd()
        os.makedirs(self._directory_path, exist_ok=True)
        os.chdir(self._directory_path)

    def revert(self) -> None:
        owd = self._owd
        if owd is not None:
            os.chdir(owd)
