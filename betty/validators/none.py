"""
``None`` validators.
"""

from __future__ import annotations

from typing import Any, final

from betty.localizables.gettext import _
from betty.pipeline import Inlet
from betty.validators import InvalidValue


@final
class NotNone(InvalidValue):
    """
    Raised when a value is not ``None``.
    """

    _message = _("This must be none/null.")


@Inlet
def is_none(value: Any, /) -> None:
    """
    Validate that a value is ``None``.
    """
    if value is not None:
        raise NotNone(value)
    return
