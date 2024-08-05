"""
Provide error handling utilities.
"""

import traceback
from pathlib import Path
from typing import TypeVar, Self

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.locale.localized import LocalizedStr
from betty.locale.localizer import Localizer

_BaseExceptionT = TypeVar("_BaseExceptionT", bound=BaseException)


def serialize(error: _BaseExceptionT) -> _BaseExceptionT:
    """
    Serialize an exception.

    This replaces the exception's traceback object with the traceback formatted as a string.
    """
    formatted_traceback = f'\n"""\n{"".join(traceback.format_exception(type(error), error, error.__traceback__))}"""'
    error.__cause__ = _SerializedTraceback(formatted_traceback)
    error.__traceback__ = None
    return error


class _SerializedTraceback(Exception):
    def __init__(self, formatted_traceback: str):
        self._formatted_traceback = formatted_traceback

    def __str__(self) -> str:
        return self._formatted_traceback


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
