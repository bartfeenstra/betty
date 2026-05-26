"""
File path assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions.path import assert_path
from betty.error import FileNotFound

if TYPE_CHECKING:
    from pathlib import Path

    from betty.functools import Pipeline


def assert_file() -> Pipeline[Any, Path]:
    """
    Assert that a value is a path to an existing file.
    """

    def _assert_file(file: Path, /) -> Path:
        if file.is_file():
            return file
        raise FileNotFound(file)

    return assert_path() | _assert_file
