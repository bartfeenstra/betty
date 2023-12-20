import traceback
from typing import TypeVar, Self

from betty.locale import Localizable, DEFAULT_LOCALIZER, Localizer

BaseExceptionT = TypeVar('BaseExceptionT', bound=BaseException)


def serialize(error: BaseExceptionT) -> BaseExceptionT:
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
        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._localizable_message = message

    def __reduce__(self) -> tuple[type[Self], tuple[Localizable]]:
        return type(self), (self._localizable_message,)

    def __str__(self) -> str:
        return self.localize(DEFAULT_LOCALIZER)

    def localize(self, localizer: Localizer) -> str:
        return self._localizable_message.localize(localizer)
