"""
Color data.
"""

from __future__ import annotations

import re
from typing import Final, final

from betty.assertions.str import assert_str
from betty.data import DataDefinition
from betty.exception import HumanFacingException
from betty.localizables.gettext import _
from betty.porters.callback import CallbackPorter
from betty.sample import Sample

_hex_pattern: Final[re.Pattern[str]] = re.compile(r"^#[a-zA-Z0-9]{6}$")


def _assert_hex(color: str) -> str:
    if not _hex_pattern.match(color):
        raise HumanFacingException(
            _('"{color}" is not a valid hexadecimal color, such as #ffc0cb.').format(
                color=color,
            )
        )
    return color


@final
class ColorDefinition(DataDefinition[str, str]):
    """
    Define a color.
    """

    def __init__(self):
        super().__init__(
            cls=str,
            label=_("Color"),
            description=_("A hexadecimal color, such as #ff0000"),
            samples=[lambda: Sample("#ff0000", label="Default")],
            porter=CallbackPorter[str, str](assert_str() | _assert_hex, str),
        )
