"""
Integral number assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions.number import _assert_number
from betty.assertions.type import assert_type

if TYPE_CHECKING:
    from betty.functools import Pipeline
    from betty.typing import Number


def assert_int(
    *, minimum: Number | None = None, maximum: Number | None = None
) -> Pipeline[Any, int]:
    """
    Assert that a value is a Python ``int``.
    """
    return assert_type(int) | _assert_number(minimum, maximum)
