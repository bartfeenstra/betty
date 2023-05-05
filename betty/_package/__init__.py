"""Provide tools for the various package managers Betty integrates with."""
from glob import glob
from os import path
from setuptools import find_packages as find_packages_setuptools
from typing import List, Dict

from betty.os import ChDir

ROOT_DIRECTORY_PATH = path.dirname(path.dirname(path.dirname(__file__)))


def find_packages():
    return find_packages_setuptools(
        '.',
        exclude=[
            'betty._package',
            'betty._package.*',
            'betty.tests',
            'betty.tests.*',
        ],
    )


def is_data_file(file_path):
    if not path.isfile(file_path):
        return False
    if '__pycache__' in file_path:
        return False
    return True


def get_data_paths() -> Dict[str, List[str]]:
    with ChDir(f'{ROOT_DIRECTORY_PATH}/betty'):
        return {
            'betty': list(filter(is_data_file, [
                *glob('assets/**', recursive=True),
                *glob('plugin/*/assets/**', recursive=True),
            ])),
        }
