"""
Test utilities for :py:mod:`betty.exception`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, overload

from betty.exception import HumanFacingException, HumanFacingExceptionGroup
from betty.locale.localizer import DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    from betty.data import Context


@overload
def assert_error(
    actual_error: HumanFacingException | HumanFacingExceptionGroup,
    *,
    error: HumanFacingException,
    error_type: type[HumanFacingException] = HumanFacingException,
    error_message: None = None,
    error_contexts: None = None,
) -> Sequence[HumanFacingException]:
    pass


@overload
def assert_error(
    actual_error: HumanFacingException | HumanFacingExceptionGroup,
    *,
    error: None = None,
    error_type: type[HumanFacingException] = HumanFacingException,
    error_message: str | None = None,
    error_contexts: Sequence[Context] | None = None,
) -> Sequence[HumanFacingException]:
    pass


def assert_error(
    actual_error: HumanFacingException | HumanFacingExceptionGroup,
    *,
    error: HumanFacingException | None = None,
    error_type: type[HumanFacingException] = HumanFacingException,
    error_message: str | None = None,
    error_contexts: Sequence[Context] | None = None,
) -> Sequence[HumanFacingException]:
    """
    Assert that an error group contains an error matching the given parameters.
    """
    expected_error_contexts: Sequence[str] | None
    actual_errors: Iterable[HumanFacingException]
    if isinstance(actual_error, HumanFacingExceptionGroup):
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
            context.localize(DEFAULT_LOCALIZER) for context in error.contexts
        ]
    else:
        expected_error_type = error_type
        if error_message is not None:
            expected_error_message = error_message
        if error_contexts is not None:
            expected_error_contexts = [
                context.localize(DEFAULT_LOCALIZER) for context in error_contexts
            ]

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
            == [
                context.localize(DEFAULT_LOCALIZER) for context in actual_error.contexts
            ]
        ]
    if errors:
        return errors
    raise AssertionError("Failed raising UserFacingException.")


@contextmanager
def raises_error(*args: Any, **kwargs: Any) -> Iterator[HumanFacingExceptionGroup]:
    """
    Provide a context manager to assert that an error group contains an error matching the given parameters.
    """
    try:
        with HumanFacingExceptionGroup().catch() as errors:
            yield errors
    finally:
        assert_error(errors, *args, **kwargs)
        errors.assert_valid()
