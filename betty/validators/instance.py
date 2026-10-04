"""
Instance check validators.
"""

from __future__ import annotations

from typing import Any

from betty.functools import Pipeline
from betty.validation import Invalid, group


def is_instance[ValueT](alleged_type: type[ValueT], /) -> Pipeline[Any, ValueT]:
    """
    Validate that a value is an instance of the given type.

    This validator is **NOT** optimized to be user-facing (it is untranslated)
    because Python types are not user-facing.
    """

    @group()
    def _is_instance(value: Any, /) -> ValueT:
        if isinstance(value, alleged_type):
            return value
        raise Invalid(f"{value} must be an instance of {alleged_type}.")

    return Pipeline(_is_instance)
