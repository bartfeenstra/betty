"""
String data assertions.
"""

from __future__ import annotations

from typing import Any

from betty.assertions import _HumanFacingValueError
from betty.assertions.type import assert_type
from betty.functools import Pipeline
from betty.locale.localizable.gettext import _


def assert_str(
    *,
    exact_length: int | None = None,
    minimum_length: int | None = None,
    maximum_length: int | None = None,
) -> Pipeline[Any, str]:
    """
    Assert that a value is a Python ``str``.
    """

    def _assert_str(value: Any, /) -> str:
        string = assert_type(str)(value)
        actual = len(value)
        if exact_length is not None and actual != exact_length:
            raise _HumanFacingValueError(
                _("This must be {length} characters long.").format(
                    length=str(exact_length)
                )
            )
        if minimum_length is not None and actual < minimum_length:
            raise _HumanFacingValueError(
                _("This must be at least {length} characters long.").format(
                    length=str(minimum_length)
                )
            )
        if maximum_length is not None and actual > maximum_length:
            raise _HumanFacingValueError(
                _("This must be at most {length} characters long.").format(
                    length=str(maximum_length)
                )
            )
        return string

    return Pipeline(_assert_str)
