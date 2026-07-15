"""
Directory path assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions import _HumanFacingValueError
from betty.assertions.path import assert_path
from betty.localizables.gettext import _
from betty.localizables.markup import Quote

if TYPE_CHECKING:
    from pathlib import Path

    from betty.functools import Pipeline


def assert_directory() -> Pipeline[Any, Path]:
    """
    Assert that a value is a path to an existing directory.
    """

    def _assert_directory(directory: Path, /) -> Path:
        if directory.is_dir():
            return directory
        raise _HumanFacingValueError(
            _("{path} is not a directory.").format(path=Quote(str(directory)))
        )

    return assert_path() | _assert_directory
