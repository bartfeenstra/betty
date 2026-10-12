"""
Validate data against predefined options.
"""

from __future__ import annotations

from typing import Any, final

from betty.localizables.gettext import _
from betty.localizables.markup import do_you_mean
from betty.pipeline import Inlet, Pipeline
from betty.validators import InvalidValue


@final
class UnknownOption(InvalidValue):
    """
    Raised when a value cannot be validated against predefined options.
    """

    _message = _("Unknown option.")


def is_option[OptionT](*options: OptionT) -> Pipeline[Any, OptionT]:
    """
    Validate a value against predefined options.
    """

    def _is_option(value: Any) -> OptionT:
        if value in options:
            return value
        raise UnknownOption(value, hint=do_you_mean(*map(str, options))) from None

    return Inlet(_is_option)
