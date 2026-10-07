"""
Floating-point number validators.
"""

from __future__ import annotations

from typing import Any, final

from betty.localizables.gettext import _
from betty.validators import _StaticMessageInvalid
from betty.validators.number import IsNumber


@final
class NotAFloat(_StaticMessageInvalid):
    """
    Raised when a value is not a ``float``.
    """

    _message = _("This must be a decimal number.")


@IsNumber
def is_float(value: Any, /) -> float:
    """
    Validate that a value is a Python ``float`` or can be safely converted to one.
    """
    if isinstance(value, float):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    raise NotAFloat(value)
