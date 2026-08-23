"""
Floating-point number assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions.number import _assert_number
from betty.assertions.type import assert_type

if TYPE_CHECKING:
    from betty.functools import Pipeline


def assert_float(
    *, minimum: float | None = None, maximum: float | None = None
) -> Pipeline[Any, float]:
    """
    Assert that a value is a Python ``float``.
    """
    return assert_type(float) | _assert_number(minimum, maximum)
