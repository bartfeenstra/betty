"""
File system path validators.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from betty.validators.if_else import is_if_else
from betty.validators.instance import is_instance
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.functools import Pipeline


def is_path() -> Pipeline[Any, Path]:
    """
    Validate that a value is a path to a file or directory on disk that may or may not exist.
    """
    return is_if_else(is_instance(Path), is_str | Path)
