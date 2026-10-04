"""
Conditional validators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.functools import Pipeline
from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.markup import Paragraphs
from betty.validation import Invalid, Validator, group

if TYPE_CHECKING:
    from collections.abc import MutableSequence


def is_if_else[ValueT, ReturnT, validatorReturnU](
    is_if: Validator[ValueT, ReturnT],
    is_else: Validator[ValueT, validatorReturnU],
    /,
) -> Pipeline[ValueT, ReturnT | validatorReturnU]:
    """
    Validate that at least one of the given validators passes.
    """

    @group()
    def _is_if_else(value: Any, /) -> ReturnT | validatorReturnU:
        validators = (is_if, is_else)
        errors: MutableSequence[ResolvableLocalizable] = []
        for validator in validators:
            try:
                return validator(value)
            except Exception as error:
                errors.append(error if isinstance(error, Localizable) else str(error))
        raise Invalid(Paragraphs(*errors))

    return Pipeline(_is_if_else)
