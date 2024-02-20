"""
Provide error handling utilities.
"""
from traceback import format_exception
from typing import TypeVar, Self

from betty.locale import Localizable, DEFAULT_LOCALIZER, Localizer

BaseExceptionT = TypeVar('BaseExceptionT', bound=BaseException)


def serialize(error: BaseExceptionT) -> BaseExceptionT:
    """
    Serialize an exception.

    This replaces the exception's traceback object with the traceback formatted as a string.
    """
    error.__cause__ = _SerializedTraceback(''.join(format_exception(error)))
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
        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._message = message

    def __reduce__(self) -> tuple[type[Self], tuple[Localizable]]:
        return type(self), (self._message,)

    def __str__(self) -> str:
        return self.message.localize(DEFAULT_LOCALIZER)

    @property
    def message(self) -> Localizable:
        return self._message

    def localize(self, localizer: Localizer) -> str:
        return self.message.localize(localizer)
