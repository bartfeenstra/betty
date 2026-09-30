"""
Directory path validators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.validation import Invalid, group
from betty.validators.path import is_path

if TYPE_CHECKING:
    from pathlib import Path


@group()
def _is_directory(directory: Path, /) -> Path:
    if directory.is_dir():
        return directory
    raise Invalid(_("{path} is not a directory.").format(path=Quote(str(directory))))


is_directory = is_path() | _is_directory
"""
Validate that a value is a path to an existing directory.
"""
