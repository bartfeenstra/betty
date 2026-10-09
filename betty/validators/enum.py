"""
Enum data validators.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, final

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.localizables.markup import do_you_mean
from betty.validators import _StaticInvalid


@final
class UnknownOption(_StaticInvalid):
    """
    Raised when a value cannot be validated against an enum.
    """

    _message = _("Unknown option.")


def is_enum[EnumT: Enum](options: type[EnumT], /) -> Pipe[Any, EnumT]:
    """
    Validate that a value is allowed by an enum, and return the enum value.
    """

    def _is_enum(value: Any) -> Any:
        try:
            return options(value)
        except ValueError:
            raise UnknownOption(
                value, hint=do_you_mean(*[option.value for option in options])
            ) from None

    return Pipe(_is_enum)
