"""
File path tools.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

# This mimics _typeshed.StrPath
type StrPath = str | PathLike[str]


def resolve_path(path: StrPath) -> Path:
    """
    Resolve a path-like value to a path.
    """
    if isinstance(path, Path):
        return path
    return Path(path)
