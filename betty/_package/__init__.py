"""Provide tools for the various package managers Betty integrates with."""
from glob import glob
from pathlib import Path
from typing import Iterator

from setuptools import find_packages as find_packages_setuptools

from betty import _ROOT_DIRECTORY_PATH as ROOT_DIRECTORY_PATH
from betty.os import ChDir


def find_packages() -> list[str]:
    return find_packages_setuptools(
        '.',
        exclude=[
            'betty._package',
            'betty._package.*',
            'betty.tests',
            'betty.tests.*',
        ],
    )


def is_data_file(file_path: Path) -> bool:
    if not (ROOT_DIRECTORY_PATH / 'betty' / file_path).is_file():
        return False
    if '__pycache__' in str(file_path):
        return False
    return True


async def get_data_paths() -> dict[str, Iterator[Path]]:
    async with ChDir(ROOT_DIRECTORY_PATH / 'betty'):
        return {
            'betty': filter(is_data_file, [
                Path('py.typed'),
                *map(Path, glob('assets/**', recursive=True)),
                *map(Path, glob('*/assets/**', recursive=True)),
            ]),
        }
