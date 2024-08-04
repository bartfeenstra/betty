"""
Test utilities for :py:mod:`betty.assertion.error`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import overload, Any, Iterator, TYPE_CHECKING

from betty.assertion.error import AssertionFailed, AssertionFailedGroup
from betty.locale.localizer import DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


@overload
def assert_error(
    actual_error: AssertionFailed | AssertionFailedGroup,
    *,
    error: AssertionFailed,
    error_type: None = None,
    error_message: None = None,
    error_contexts: None = None,
) -> Sequence[AssertionFailed]:
    pass


@overload
def assert_error(
    actual_error: AssertionFailed | AssertionFailedGroup,
    *,
    error: None = None,
    error_type: type[AssertionFailed] = AssertionFailed,
    error_message: str | None = None,
    error_contexts: Sequence[str] | None = None,
) -> Sequence[AssertionFailed]:
    pass


def assert_error(
    actual_error: AssertionFailed | AssertionFailedGroup,
    *,
    error: AssertionFailed | None = None,
    error_type: type[AssertionFailed] | None = AssertionFailed,
    error_message: str | None = None,
    error_contexts: Sequence[str] | None = None,
) -> Sequence[AssertionFailed]:
    """
    Assert that an error group contains an error matching the given parameters.
    """
    expected_error_contexts: Sequence[str] | None
    actual_errors: Iterable[AssertionFailed]
    if isinstance(actual_error, AssertionFailedGroup):
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
    raise AssertionError("Failed raising a serialization or deserialization error.")


@contextmanager
def raises_error(*args: Any, **kwargs: Any) -> Iterator[AssertionFailedGroup]:
    """
    Provide a context manager to assert that an error group contains an error matching the given parameters.
    """
    try:
        with AssertionFailedGroup().catch() as errors:
            yield errors
    finally:
        assert_error(errors, *args, **kwargs)
        errors.assert_valid()
