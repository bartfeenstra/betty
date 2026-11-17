"""
Validator groupings.
"""

from __future__ import annotations

from typing import Any

from betty.error import Requires
from betty.pipeline import Inlet, Pipeline
from betty.validation import Invalid, InvalidGroup, Validator


def is_any[InputT, OutputT](
    *validators: Validator[InputT, OutputT],
) -> Pipeline[InputT, OutputT]:
    """
    Validate that any of the validators passes.

    The validators are called in order. The return value is the return value of the first validator not to error.
    """

    def _is_any(value: Any, /) -> OutputT:
        errors = []
        for validator in validators:
            try:
                return validator(value)
            except Invalid as error:
                errors.append(error)
        raise InvalidGroup(value, *errors, requires=Requires.ANY_OF)

    return Inlet(_is_any)
