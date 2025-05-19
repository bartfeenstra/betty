"""
Provide error handling utilities.
"""

from pathlib import Path
from typing import Self

from betty.exception import UserFacingException
from betty.locale.localizable import _


class FileNotFound(UserFacingException, FileNotFoundError):
    """
    Raised when a file cannot be found.
    """

    @classmethod
    def new(cls, file_path: Path) -> Self:
        """
        Create a new instance for the given file path.
        """
        return cls(
            _('Could not find the file "{file_path}".').format(file_path=str(file_path))
        )
