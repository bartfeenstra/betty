"""
Numeric data validators.
"""

from __future__ import annotations

from functools import partial
from typing import Any, final, overload, override

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.validation import Invalid, Validator


@final
class TooLow(Invalid):
    """
    Raised when a number is too low.
    """


@final
class TooHigh(Invalid):
    """
    Raised when a number is too high.
    """


def _is_number[NumberT: float | int](
    value: Any,
    /,
    type_: Validator[Any, NumberT],
    min_: NumberT | None = None,
    max_: NumberT | None = None,
) -> NumberT:
    value: NumberT = type_(value)
    if min_ is not None and value < min_:
        raise TooLow(
            value, _("This must be at least {minimum}.").format(minimum=str(min_))
        )
    if max_ is not None and value > max_:
        raise TooHigh(
            value, _("This must be at most {maximum}.").format(maximum=str(max_))
        )
    return value


@final
class IsNumber[NumberT: float | int](Pipe[Any, NumberT]):
    """
    Validate that a value is a number.
    """

    def __init__(self, type_: Validator[Any, NumberT], /):
        super().__init__(partial(_is_number, type_=type_))
        self._type = type_

    @overload
    def __call__(
        self, value: Any, /, *, min: NumberT | None = None, max: NumberT | None = None
    ) -> NumberT:
        pass

    @overload
    def __call__(
        self, *, min: NumberT | None = None, max: NumberT | None = None
    ) -> Pipe[Any, NumberT]:
        pass

    @override
    def __call__(self, *value_, min: NumberT | None = None, max: NumberT | None = None):
        if value_:
            return _is_number(value_[0], self._type, min, max)
        return Pipe(partial(_is_number, type_=self._type, min_=min, max_=max))
