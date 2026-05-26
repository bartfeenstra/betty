"""
Instance check assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions import _HumanFacingValueError

if TYPE_CHECKING:
    from betty.functools import Pipe


def assert_isinstance[ValueT](alleged_type: type[ValueT], /) -> Pipe[Any, ValueT]:
    """
    Assert that a value is an instance of the given type.

    This assertion is **NOT** optimized to be user-facing (it is untranslated)
    because Python types are not user-facing.
    """

    def _assert(value: Any, /) -> ValueT:
        if isinstance(value, alleged_type):
            return value
        raise _HumanFacingValueError(f"{value} must be an instance of {alleged_type}.")

    return _assert
