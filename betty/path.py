import os
from os.path import join
from typing import Iterable


def iterfiles(path: str) -> Iterable[str]:
    return [join(dir_path, filename) for dir_path, _, filenames in os.walk(path) for filename in filenames]
