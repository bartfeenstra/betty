"""
Assertions to validate data's Python types.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import cache
from types import NoneType
from typing import TYPE_CHECKING, Any

from betty.assertions import _HumanFacingValueError
from betty.functools import Pipeline
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.localizable import Localizable

type AssertTypeType = (
    bool | float | int | Mapping[Any, Any] | None | Sequence[Any] | str
)


_ASSERT_TYPES: Mapping[type[AssertTypeType], tuple[type[Any] | None, Localizable]] = {
    bool: (None, _("This must be a boolean.")),
    int: (bool, _("This must be a whole number.")),
    float: (None, _("This must be a decimal number.")),
    Mapping: (None, _("This must be a key-value mapping.")),
    NoneType: (None, _("This must be none/null.")),
    Sequence: (None, _("This must be a sequence.")),
    str: (None, _("This must be a string.")),
}


@cache
def assert_type[AssertTypeTypeT: AssertTypeType](
    value_type: type[AssertTypeTypeT], /
) -> Pipeline[Any, AssertTypeTypeT]:
    """
    Assert that a value is of the specified built-in type.
    """

    def _assert_type(value: Any, /) -> AssertTypeTypeT:
        value_is_not_type, error_message = _ASSERT_TYPES[value_type]
        if isinstance(value, value_type) and (
            value_is_not_type is None or not isinstance(value, value_is_not_type)
        ):
            return value
        raise _HumanFacingValueError(error_message)

    return Pipeline(_assert_type)
