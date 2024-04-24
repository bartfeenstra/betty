"""Test the betty.serde module."""

from __future__ import annotations

from contextlib import contextmanager
from typing import overload, Iterable, Iterator, Any

from betty.locale import DEFAULT_LOCALIZER
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
) -> list[SerdeError]:
    pass


@overload
def assert_error(
    actual_error: SerdeError | SerdeErrorCollection,
    *,
    error: None = None,
    error_type: type[SerdeError] = SerdeError,
    error_message: str | None = None,
    error_contexts: list[str] | None = None,
) -> list[SerdeError]:
    pass


def assert_error(
    actual_error: SerdeError | SerdeErrorCollection,
    *,
    error: SerdeError | None = None,
    error_type: type[SerdeError] | None = SerdeError,
    error_message: str | None = None,
    error_contexts: list[str] | None = None,
) -> list[SerdeError]:
    """
    Assert that an error collection contains an error matching the given parameters.
    """
    expected_error_contexts: list[str] | None
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
        expected_error_contexts = [
            error.localize(DEFAULT_LOCALIZER) for error in error.contexts
        ]
    else:
        expected_error_type = error_type  # type: ignore[assignment]
        if error_message is not None:
            expected_error_message = error_message
        if error_contexts is not None:
            expected_error_contexts = error_contexts

    errors = [
        actual_error
        for actual_error in actual_errors
        if isinstance(actual_error, expected_error_type)
    ]
    if expected_error_message is not None:
        errors = [
            actual_error
            for actual_error in actual_errors
            if str(actual_error).startswith(expected_error_message)
        ]
    if expected_error_contexts is not None:
        errors = [
            actual_error
            for actual_error in actual_errors
            if expected_error_contexts
            == [error.localize(DEFAULT_LOCALIZER) for error in actual_error.contexts]
        ]
    if errors:
        return errors
    raise SerdeAssertionError(
        "Failed raising a serialization or deserialization error."
    )


@contextmanager
def raises_error(*args: Any, **kwargs: Any) -> Iterator[SerdeErrorCollection]:
    """
    Provide a context manager to assert that an error collection contains an error matching the given parameters.
    """
    try:
        with SerdeErrorCollection().catch() as errors:
            yield errors
    finally:
        assert_error(errors, *args, **kwargs)
        errors.assert_valid()
