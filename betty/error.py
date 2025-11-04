"""
Provide error handling utilities.
"""

from pathlib import Path
from typing import Self

from betty.exception import HumanFacingException
from betty.locale.localizable import _


class FileNotFound(HumanFacingException, FileNotFoundError):
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
