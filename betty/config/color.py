"""
Configuration for colors.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.assertion import assert_str
from betty.config import Configuration
from betty.data import Sample
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.portable import PortableData


class ColorConfiguration(Configuration):
    """
    Configure a color.

    .. configuration:: betty.config.color:ColorConfiguration
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
        self._assert_hex(hex_value)
        self._hex = hex_value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls((assert_str() | cls._assert_hex)(portable))

    @override
    def dump(self) -> PortableData:
        return self._hex

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.hex == other.hex

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:  # ty:ignore[invalid-method-override]
        yield Sample(cls("#ff0000"), label="Default")
