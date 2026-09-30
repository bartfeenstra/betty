"""
``None`` validators.
"""

from __future__ import annotations

from typing import Any

from betty.localizables.gettext import _
from betty.validation import Invalid


def is_none(value: Any, /) -> None:
    """
    Validate that a value is ``None``.
    """
    if value is not None:
        raise Invalid(_("This must be none/null."))
    return
