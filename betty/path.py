from pathlib import Path

from betty.os import PathLike


def rootname(source_path: PathLike) -> Path:
    source_path = Path(source_path)
    root = source_path
    while True:
        possible_root = root.parent
        if possible_root == root:
            return root
        root = possible_root
