"""
Boolean data validators.
"""

from __future__ import annotations

from typing import Any, final

from betty.localizables.gettext import _
from betty.validators import _StaticInvalid


@final
class NotABool(_StaticInvalid):
    """
    Raised when a value is not a ``bool``.
    """

    _message = _("This must be a boolean.")


def is_bool(value: Any, /) -> bool:
    """
    Validate that a value is a Python ``bool``.
    """
    if not isinstance(value, bool):
        raise NotABool(value)
    return value
