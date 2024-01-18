"""
Provide path handling utilities.
"""
from pathlib import Path


def rootname(source_path: Path) -> Path:
    r"""
    Get a path's root name, such as `/` or `C:\`.
    """
    root = source_path
    while True:
        possible_root = root.parent
        if possible_root == root:
            return root
        root = possible_root
