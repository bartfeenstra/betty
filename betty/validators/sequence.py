"""
Sequence data validators.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, final, overload, override

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.operator import Index
from betty.validation import collect
from betty.validators import _StaticMessageInvalid
from betty.validators.always import is_always_valid

if TYPE_CHECKING:
    from betty.validation import Validator


@final
class NotASequence(_StaticMessageInvalid):
    """
    Raised when a value is not a sequence.
    """

    _message = _("This must be a sequence.")


def _is_sequence[ValueT](
    value: Any, /, *, values: Validator[Any, ValueT] = is_always_valid
) -> Sequence[ValueT]:
    if not isinstance(value, Sequence):
        raise NotASequence(value)
    if values is is_always_valid:
        return value
    validated_sequence = []
    with collect(value) as errors:
        for value_index, value_value in enumerate(value):
            with (
                errors.collect(
                    value_value, location=[Index(value_index)]
                ) as value_errors,
                value_errors.catch(),
            ):
                validated_sequence.append(values(value_value))
    return validated_sequence


@final
class _IsSequence(Pipe[Any, Sequence[Any]]):
    def __init__(self):
        super().__init__(_is_sequence)

    @overload
    def __call__[ValueT](
        self, value: Any, /, *, values: Validator[Any, ValueT] = is_always_valid
    ) -> Sequence[ValueT]:
        pass

    @overload
    def __call__[ValueT](
        self, *, values: Validator[Any, ValueT] = is_always_valid
    ) -> Pipe[Any, Sequence[ValueT]]:
        pass

    @override
    def __call__(self, *value_, values=is_always_valid):
        if value_:
            return _is_sequence(value_[0], values=values)
        return Pipe(partial(_is_sequence, values=values))


is_sequence = _IsSequence()
"""
Validate that a value is a sequence.

Optionally validate that values are of a given type.
"""
