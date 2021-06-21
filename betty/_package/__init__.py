"""Provide tools for the various package managers Betty integrates with."""
from glob import glob
from pathlib import Path
from typing import List

from betty.fs import ROOT_DIRECTORY_PATH


def get_data_paths() -> List[Path]:
    return [data_path for data_path in [
        ROOT_DIRECTORY_PATH / 'VERSION',
        *map(Path, glob(str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / '**'), recursive=True)),
        *map(Path, glob(str(ROOT_DIRECTORY_PATH / 'betty' / 'extension' / '*' / 'assets' / '**'), recursive=True)),
    ] if data_path.is_file()]
