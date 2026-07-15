"""
Provide error handling utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.exception import HumanFacingException
from betty.localizables.gettext import _
from betty.localizables.markup import Quote

if TYPE_CHECKING:
    from betty.pathlib import StrPath


class FileNotFound(HumanFacingException, FileNotFoundError):
    """
    Raised when a file cannot be found.
    """

    def __init__(self, file: StrPath, /):
        super().__init__(
            _("Could not find the file {file_path}.").format(file_path=Quote(str(file)))
        )
