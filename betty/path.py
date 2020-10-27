from os import path
from os.path import splitext
from typing import Optional


def rootname(source_path: str) -> str:
    root = source_path
    while True:
        possible_root = path.dirname(root)
        if possible_root == root:
            return root
        root = possible_root


def extension(path: str) -> Optional[str]:
    extension = splitext(path)[1][1:]
    return extension if extension else None
