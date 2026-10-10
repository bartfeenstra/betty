"""
Integral number validators.
"""

from __future__ import annotations

from typing import Any, final

from betty.localizables.gettext import _
from betty.validators import _StaticInvalid
from betty.validators.number import IsNumber


@final
class NotAnInt(_StaticInvalid):
    """
    Raised when a value is not an ``int``.
    """

    _message = _("This must be a whole number.")


@IsNumber
def is_int(value: Any, /) -> int:
    """
    Validate that a value is a Python ``int``.
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise NotAnInt(value)
