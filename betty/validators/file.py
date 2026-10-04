"""
File path validators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.os import FileNotFound
from betty.validation import group
from betty.validators.path import is_path

if TYPE_CHECKING:
    from pathlib import Path


@group()
def _is_file(file: Path, /) -> Path:
    if file.is_file():
        return file
    raise FileNotFound(file)


is_file = is_path() | _is_file
"""
Validate that a value is a path to an existing file.
"""
