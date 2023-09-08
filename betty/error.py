import traceback
from typing import Any, TypeVar

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


class UserFacingError(Exception):
    """
    A user-facing error.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. It must therefore have an end-user-friendly message, and its stack trace must not be shown.
    """
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
