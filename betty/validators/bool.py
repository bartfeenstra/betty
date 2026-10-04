"""
Boolean data validators.
"""

from __future__ import annotations

from typing import Any

from betty.localizables.gettext import _
from betty.validation import Invalid


def is_bool(value: Any, /) -> bool:
    """
    Validate that a value is a Python ``bool``.
    """
    if not isinstance(value, bool):
        raise Invalid(_("This must be a boolean."))
    return value
