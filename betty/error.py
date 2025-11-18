"""
Provide error handling utilities.
"""

from pathlib import Path

from betty.exception import HumanFacingException
from betty.locale.localizable import _


class FileNotFound(HumanFacingException, FileNotFoundError):
    """
    Raised when a file cannot be found.
    """

    def __init__(self, file_path: Path, /):
        super().__init__(
            _('Could not find the file "{file_path}".').format(file_path=str(file_path))
        )
