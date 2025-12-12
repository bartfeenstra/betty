"""
Configuration for colors.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.assertion import assert_str
from betty.config import Configuration
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class ColorConfiguration(Configuration):
    """
    Configure a color.
    """

    _HEX_PATTERN = re.compile(r"^#[a-zA-Z0-9]{6}$")

    def __init__(self, hex_value: str, /):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    @classmethod
    def _assert_hex(cls, hex_value: str) -> str:
        if not cls._HEX_PATTERN.match(hex_value):
            raise HumanFacingException(
                _(
                    '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.'
                ).format(
                    hex_value=hex_value,
                )
            )
        return hex_value

    @property
    def hex(self) -> str:
        """
        The color's hexadecimal value.
        """
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        self.assert_mutable()
        self._assert_hex(hex_value)
        self._hex = hex_value

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls((assert_str() | cls._assert_hex)(dump))

    @override
    def dump(self) -> Dump:
        return self._hex
