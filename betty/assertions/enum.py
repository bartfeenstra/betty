"""
Enum data assertions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from betty.assertions import _HumanFacingValueError
from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, do_you_mean


def assert_enum[EnumT: Enum](options: type[EnumT]) -> Pipeline[Any, EnumT]:
    """
    Assert that a value is allowed by an enum, and return the enum value.
    """

    def _assert_enum(value: Any) -> Any:
        try:
            return options(value)
        except ValueError:
            raise _HumanFacingValueError(
                Paragraph(
                    _("Invalid option {value}.").format(value=str(value)),
                    do_you_mean(*[option.value for option in options]),
                )
            ) from None

    return Pipeline(_assert_enum)
