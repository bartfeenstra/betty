"""
Color validators.
"""

from __future__ import annotations

import re
from typing import final

from betty import samples
from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.validators import _StaticMessageInvalid

_hex_pattern = re.compile(r"^#[a-zA-Z0-9]{6}$")


@final
class NotAHex(_StaticMessageInvalid):
    """
    Raised when a value is not a hexadecimal color.
    """

    _message = _("This is not a valid hexadecimal color, such as {color}.").format(
        color=Quote(samples.color_hex)
    )


@Pipe
def is_hex(value: str, /) -> str:
    """
    Validate that a value is a hexadecimal color.
    """
    if not _hex_pattern.fullmatch(value):
        raise NotAHex(value)
    return value
