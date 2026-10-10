"""
String data validators.
"""

from __future__ import annotations

from typing import Any, final

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.validators import _StaticInvalid
from betty.validators.len import IsLen, IsMaxLen, IsMinLen


@final
class NotAStr(_StaticInvalid):
    """
    Raised when a value is not a ``str``.
    """

    _message = _("This must be a string.")


@Pipe
def is_str(value: Any, /) -> str:
    """
    Validate that a value is a Python ``str``.
    """
    if not isinstance(value, str):
        raise NotAStr(value)
    return value


is_str_len = IsLen[str](_("This must be {length} characters long."))
is_str_min_len = IsMinLen[str](_("This must be at least {length} characters long."))
is_str_max_len = IsMaxLen[str](_("This must be at most {length} characters long."))
