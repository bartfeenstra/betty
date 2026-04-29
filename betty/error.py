"""
Provide error handling utilities.
"""

from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.pathlib import StrPath


class FileNotFound(HumanFacingException, FileNotFoundError):
    """
    Raised when a file cannot be found.
    """

    def __init__(self, file: StrPath, /):
        super().__init__(
            _('Could not find the file "{file_path}".').format(file_path=str(file))
        )
