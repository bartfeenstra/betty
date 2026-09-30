"""
Numeric data validators.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, final, overload, override

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.validation import Invalid, group

if TYPE_CHECKING:
    import builtins


@group()
def _is_number[NumberT](
    value: Any,
    type_: type[NumberT],
    min_: NumberT | None = None,
    max_: NumberT | None = None,
) -> NumberT:
    if not isinstance(value, type_):
        raise Invalid(_("This must be a number."))
    if min_ is not None and value < min_:
        raise Invalid(_("This must be at least {minimum}.").format(minimum=str(min_)))
    if max_ is not None and value > max_:
        raise Invalid(_("This must be at most {maximum}.").format(maximum=str(max_)))
    return value


@final
class IsNumberType[NumberT](Pipeline[Any, NumberT]):
    """
    Validate that a value is a number.
    """

    def __init__(
        self,
        *,
        type: builtins.type[NumberT],  # noqa: A002
    ):
        super().__init__(_is_number)
        self._type = type

    @overload
    def __call__(
        self, value: Any, /, *, min: NumberT | None = None, max: NumberT | None = None
    ) -> NumberT:
        pass

    @overload
    def __call__(
        self, *, min: NumberT | None = None, max: NumberT | None = None
    ) -> Pipeline[Any, NumberT]:
        pass

    @override
    def __call__(self, *value_, **kwargs):
        if value_:
            return _is_number(value_[0], self._type, kwargs["min"], kwargs["max"])
        return Pipeline(partial(_is_number, **kwargs))
