"""
Provide error handling utilities.
"""

from pathlib import Path
from typing import Self

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.locale.localized import LocalizedStr
from betty.locale.localizer import Localizer


class UserFacingError(Exception, Localizable):
    """
    A localizable, user-facing error.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. It must therefore have an end-user-friendly message, and its stack trace must not be shown.
    """

    def __init__(self, message: Localizable):
        from betty.locale.localizer import DEFAULT_LOCALIZER

        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._localizable_message = message

    def __str__(self) -> str:
        from betty.locale.localizer import DEFAULT_LOCALIZER

        return self.localize(DEFAULT_LOCALIZER)

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        return self._localizable_message.localize(localizer)


class FileNotFound(UserFacingError, FileNotFoundError):
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
