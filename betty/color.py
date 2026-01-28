"""
Color management.
"""

from __future__ import annotations

import re
from typing import final

from betty.assertion import assert_str
from betty.data import DataDefinition, Sample
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.portable import CallbackPorter

_HEX_PATTERN = re.compile(r"^#[a-zA-Z0-9]{6}$")


def _assert_hex(color: str) -> str:
    if not _HEX_PATTERN.match(color):
        raise HumanFacingException(
            _('"{color}" is not a valid hexadecimal color, such as #ffc0cb.').format(
                color=color,
            )
        )
    return color


@final
class ColorDefinition(DataDefinition):
    """
    Define a color.
    """

    def __init__(self):
        super().__init__(
            cls=str,
            label=_("Color"),
            description=_("A hexadecimal color, such as #ff0000"),
            samples=[lambda: Sample("#ff0000", label="Default")],
            porter=CallbackPorter(assert_str() | _assert_hex, str),
        )
