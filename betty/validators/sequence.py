"""
Sequence data validators.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, overload

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.locator.operator import Index
from betty.validation import Invalid, locate

if TYPE_CHECKING:
    from betty.validation import Validator


@overload
def is_sequence(*, values: None = None) -> Pipeline[Any, Sequence[Any]]:
    pass


@overload
def is_sequence[ValueT](
    *, values: Validator[Any, ValueT]
) -> Pipeline[Any, Sequence[ValueT]]:
    pass


def is_sequence[ValueT](*, values=None):
    """
    Validate that a value is a sequence.

    Optionally validate that values are of a given type.
    """

    def _is_sequence(value: Any, /) -> Sequence[ValueT]:
        if not isinstance(value, Sequence):
            raise Invalid(_("This must be a sequence."))
        if values is None:
            return value
        validated_sequence = []
        for item_index, item_value in enumerate(value):
            with locate(Index(item_index)):
                validated_sequence.append(values(item_value))
        return validated_sequence

    return Pipeline(_is_sequence)
