"""
Numeric data assertions.
"""

from __future__ import annotations

from typing import Any

from betty.assertions import _HumanFacingValueError
from betty.assertions.if_else import assert_if_else
from betty.assertions.type import assert_type
from betty.functools import Pipeline
from betty.locale.localizable.gettext import _
from betty.typing import Number


def _assert_number[NumberT: Number](
    minimum: Number | None = None, maximum: Number | None = None
) -> Pipeline[NumberT, NumberT]:
    def __assert_number(value: NumberT) -> NumberT:
        if minimum is not None and value < minimum:
            raise _HumanFacingValueError(
                _("This must be at least {minimum}.").format(minimum=str(minimum))
            )
        if maximum is not None and value > maximum:
            raise _HumanFacingValueError(
                _("This must be at most {maximum}.").format(maximum=str(maximum))
            )
        return value

    return Pipeline(__assert_number)


def assert_number(
    *, minimum: Number | None = None, maximum: Number | None = None
) -> Pipeline[Any, Number]:
    """
    Assert that a value is a number (a Python ``int`` or ``float``).
    """
    return assert_if_else(assert_type(int), assert_type(float)) | _assert_number(
        minimum, maximum
    )
