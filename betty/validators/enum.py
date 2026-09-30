"""
Enum data validators.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, do_you_mean
from betty.validation import Invalid, group


def is_enum[EnumT: Enum](options: type[EnumT], /) -> Pipeline[Any, EnumT]:
    """
    Validate that a value is allowed by an enum, and return the enum value.
    """

    @group()
    def _is_enum(value: Any) -> Any:
        try:
            return options(value)
        except ValueError:
            raise Invalid(
                Paragraph(
                    _("Invalid option {value}.").format(value=str(value)),
                    do_you_mean(*[option.value for option in options]),
                )
            ) from None

    return Pipeline(_is_enum)
