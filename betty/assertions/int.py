"""
Integral number assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions.number import _assert_number
from betty.assertions.type import assert_type

if TYPE_CHECKING:
    from betty.functools import Pipe


def assert_int(
    *, minimum: float | None = None, maximum: float | None = None
) -> Pipe[Any, int]:
    """
    Assert that a value is a Python ``int``.
    """
    return assert_type(int) | _assert_number(minimum, maximum)
