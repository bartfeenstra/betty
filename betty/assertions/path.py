"""
File system path assertions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from betty.assertions.if_else import assert_if_else
from betty.assertions.isinstance import assert_isinstance
from betty.assertions.str import assert_str

if TYPE_CHECKING:
    from betty.functools import Pipeline


def assert_path() -> Pipeline[Any, Path]:
    """
    Assert that a value is a path to a file or directory on disk that may or may not exist.
    """
    return assert_if_else(assert_isinstance(Path), assert_str() | Path)
