from __future__ import annotations

from contextlib import contextmanager
from typing import overload, List, Type, Tuple, Iterable, Iterator

from betty.serde.error import SerdeError, SerdeErrorCollection


class SerdeAssertionError(AssertionError):
    pass


@overload
def assert_error(
    actual_error: SerdeError | SerdeErrorCollection,
    *,
    error: SerdeError,
    error_type: None = None,
    error_message: None = None,
    error_contexts: None = None,
) -> List[SerdeError]:
    pass


@overload
def assert_error(
    actual_error: SerdeError | SerdeErrorCollection,
    *,
    error: None = None,
    error_type: Type[SerdeError] = SerdeError,
    error_message: str | None = None,
    error_contexts: Tuple[str, ...] | None = None,
) -> List[SerdeError]:
    pass


def assert_error(
    actual_error: SerdeError | SerdeErrorCollection,
    *,
    error: SerdeError | None = None,
    error_type: Type[SerdeError] | None = SerdeError,
    error_message: str | None = None,
    error_contexts: Tuple[str, ...] | None = None,
) -> List[SerdeError]:
    actual_errors: Iterable[SerdeError]
    if isinstance(actual_error, SerdeErrorCollection):
        actual_errors = [*actual_error]
    else:
        actual_errors = [actual_error]

    expected_error_type: type
    expected_error_message = None
    expected_error_contexts = None
    if error:
        expected_error_type = type(error)
        expected_error_message = str(error)
        expected_error_contexts = error.contexts
    else:
        expected_error_type = error_type  # type: ignore[assignment]
        if error_message is not None:
            expected_error_message = error_message
        if error_contexts is not None:
            expected_error_contexts = error_contexts

    errors = [actual_error for actual_error in actual_errors if isinstance(actual_error, expected_error_type)]
    if expected_error_message is not None:
        errors = [actual_error for actual_error in actual_errors if str(actual_error).startswith(expected_error_message)]
    if expected_error_contexts is not None:
        errors = [actual_error for actual_error in actual_errors if expected_error_contexts == actual_error.contexts]
    if errors:
        return errors
    raise SerdeAssertionError('Failed raising a serialization or deserialization error.')


@contextmanager
def raises_error(*args, **kwargs) -> Iterator[SerdeErrorCollection]:
    try:
        with SerdeErrorCollection().catch() as errors:
            yield errors
    finally:
        assert_error(errors, *args, **kwargs)
        errors.assert_valid()
