"""
File path tools.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

# This mimics _typeshed.StrPath
type StrPath = str | PathLike[str]
type ResolvableExtension = Extension | StrPath
"""
A file extension.
"""


def resolve_path(path: StrPath) -> Path:
    """
    Resolve a path-like value to a path.
    """
    if isinstance(path, Path):
        return path
    return Path(path)


class Extension(str):
    """
    A file extension.
    """

    __slots__ = ()

    def __new__(  # noqa: D102
        cls, extension: ResolvableExtension, /
    ):
        if isinstance(extension, cls):
            return extension
        path = resolve_path(extension)
        suffix = path.suffix or path.name
        return super().__new__(cls, "." + suffix.lstrip(".").lower() if suffix else "")
