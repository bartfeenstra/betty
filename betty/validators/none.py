"""
``None`` validators.
"""

from __future__ import annotations

from typing import Any, final

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.validators import _StaticInvalid


@final
class NotNone(_StaticInvalid):
    """
    Raised when a value is not ``None``.
    """

    _message = _("This must be none/null.")


@Pipe
def is_none(value: Any, /) -> None:
    """
    Validate that a value is ``None``.
    """
    if value is not None:
        raise NotNone(value)
    return
