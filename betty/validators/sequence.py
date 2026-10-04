"""
Sequence data validators.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, final, overload, override

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.locator.operator import Index
from betty.validation import Invalid, group, locate

if TYPE_CHECKING:
    from betty.validation import Validator


@group()
def _is_sequence[ValueT](
    value: Any, /, *, values: Validator[Any, ValueT] | None = None
) -> Sequence[ValueT]:
    if not isinstance(value, Sequence):
        raise Invalid(_("This must be a sequence."))
    if values is None:
        return value
    validated_sequence = []
    for item_index, item_value in enumerate(value):
        with locate(Index(item_index)):
            validated_sequence.append(values(item_value))
    return validated_sequence


@final
class _IsSequence[ValueT](Pipeline[Any, Sequence[ValueT]]):
    def __init__(self):
        super().__init__(_is_sequence)

    @overload
    def __call__(self, value: Any, /, *, values: Validator[Any, ValueT]) -> str:
        pass

    @overload
    def __call__(self, *, values: Validator[Any, ValueT]) -> Pipeline[Any, str]:
        pass

    @override
    def __call__(self, *value_, values: Validator[Any, ValueT] | None = None):
        if value_:
            return self(value_[0], values=values)
        return Pipeline(_is_sequence(self, values=values))


is_sequence = _IsSequence()
"""
Validate that a value is a sequence.

Optionally validate that values are of a given type.
"""
