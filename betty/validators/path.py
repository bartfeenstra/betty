"""
File system path validators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, final

from betty.importlib import fully_qualified_name
from betty.localizables.gettext import _
from betty.validators import _StaticMessageInvalid
from betty.validators.if_else import is_if_else
from betty.validators.str import is_str


@final
class NotAPath(_StaticMessageInvalid):
    """
    Raised when a value is not a :py:class:`pathlib.Path`.
    """

    _message = f"This must be a {fully_qualified_name(Path)}"


def _is_path(value: Any, /) -> Path:
    if isinstance(value, Path):
        return value
    raise NotAPath(value)


is_path = is_if_else(is_str | Path, _is_path)
"""
Validate that a value is a path to a file or directory on disk that may or may not exist.
"""


@final
class NotFound(_StaticMessageInvalid, FileNotFoundError):
    """
    Raised when a path cannot be found.
    """

    _message = _("This path does not exist.")


@final
class NotADirectory(_StaticMessageInvalid, NotADirectoryError):
    """
    Raised when a value is not a directory path.
    """

    _message = _("This is not a directory.")


def _is_directory(value: Path, /) -> Path:
    if value.is_dir():
        return value
    if value.exists():
        raise NotADirectory(value)
    raise NotFound(value)


is_directory = is_path | _is_directory
"""
Validate that a value is a directory path.
"""


@final
class NotAFile(_StaticMessageInvalid, IsADirectoryError):
    """
    Raised when a value is not a file path.
    """

    _message = _("This is not a file.")


def _is_file(value: Path, /) -> Path:
    if value.is_file():
        return value
    if value.exists():
        raise NotAFile(value)
    raise NotFound(value)


is_file = is_path | _is_file
"""
Validate that a value is a file path.
"""
