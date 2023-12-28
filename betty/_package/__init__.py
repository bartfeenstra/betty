"""Provide tools for the various package managers Betty integrates with."""
import os
from glob import glob
from pathlib import Path
from typing import Iterator

from betty import _ROOT_DIRECTORY_PATH as ROOT_DIRECTORY_PATH


def is_data_file(file_path: Path) -> bool:
    if not (ROOT_DIRECTORY_PATH / 'betty' / file_path).is_file():
        return False
    if '__pycache__' in str(file_path):
        return False
    return True


def get_data_paths() -> dict[str, Iterator[Path]]:
    owd = os.getcwd()
    try:
        os.chdir(ROOT_DIRECTORY_PATH / 'betty')
        return {
            'betty': filter(is_data_file, [
                Path('py.typed'),
                *map(Path, glob('assets/**', recursive=True)),
                *map(Path, glob('extension/*/assets/**', recursive=True)),
            ]),
        }
    finally:
        os.chdir(owd)
