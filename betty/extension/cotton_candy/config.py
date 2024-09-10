"""
Provide configuration for the Cotton Candy extension.
"""

from __future__ import annotations

import re
from typing import Self, Sequence, TYPE_CHECKING

from typing_extensions import override

from betty.assertion import (
    assert_str,
    assert_record,
    OptionalField,
    assert_path,
    assert_setattr,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.locale.localizable import _
from betty.project.config import EntityReference, EntityReferenceSequence
from betty.serde.dump import Dump, VoidableDump, minimize
from betty.typing import Void

if TYPE_CHECKING:
    from betty.model import UserFacingEntity, Entity
    from pathlib import Path


class ColorConfiguration(Configuration):
    """
    Configure a color.
    """

    _HEX_PATTERN = re.compile(r"^#[a-zA-Z0-9]{6}$")

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _assert_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise AssertionFailed(
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
    def update(self, other: Self) -> None:
        self.hex = other.hex

    @override
    def load(self, dump: Dump) -> None:
        self._hex = (assert_str() | self._assert_hex)(dump)

    @override
    def dump(self) -> VoidableDump:
        return self._hex


class CottonCandyConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.extension.cotton_candy.CottonCandy` extension.
    """

    DEFAULT_PRIMARY_INACTIVE_COLOR = "#ffc0cb"
    DEFAULT_PRIMARY_ACTIVE_COLOR = "#ff69b4"
    DEFAULT_LINK_INACTIVE_COLOR = "#149988"
    DEFAULT_LINK_ACTIVE_COLOR = "#2a615a"

    def __init__(
        self,
        *,
        featured_entities: (
            Sequence[EntityReference[UserFacingEntity & Entity]] | None
        ) = None,
        primary_inactive_color: str = DEFAULT_PRIMARY_INACTIVE_COLOR,
        primary_active_color: str = DEFAULT_PRIMARY_ACTIVE_COLOR,
        link_inactive_color: str = DEFAULT_LINK_INACTIVE_COLOR,
        link_active_color: str = DEFAULT_LINK_ACTIVE_COLOR,
        logo: Path | None = None,
    ):
        super().__init__()
        self._featured_entities = EntityReferenceSequence["UserFacingEntity & Entity"](
            featured_entities or ()
        )
        self._primary_inactive_color = ColorConfiguration(primary_inactive_color)
        self._primary_active_color = ColorConfiguration(primary_active_color)
        self._link_inactive_color = ColorConfiguration(link_inactive_color)
        self._link_active_color = ColorConfiguration(link_active_color)
        self._logo = logo

    @property
    def featured_entities(self) -> EntityReferenceSequence[UserFacingEntity & Entity]:
        """
        The entities featured on the front page.
        """
        return self._featured_entities

    @property
    def primary_inactive_color(self) -> ColorConfiguration:
        """
        The color for inactive primary/CTA elements.
        """
        return self._primary_inactive_color

    @property
    def primary_active_color(self) -> ColorConfiguration:
        """
        The color for active primary/CTA elements.
        """
        return self._primary_active_color

    @property
    def link_inactive_color(self) -> ColorConfiguration:
        """
        The color for inactive hyperlinks.
        """
        return self._link_inactive_color

    @property
    def link_active_color(self) -> ColorConfiguration:
        """
        The color for active hyperlinks.
        """
        return self._link_active_color

    @property
    def logo(self) -> Path | None:
        """
        The path to the logo.
        """
        return self._logo

    @logo.setter
    def logo(self, logo: Path | None) -> None:
        self._logo = logo

    @override
    def update(self, other: Self) -> None:
        self.featured_entities.update(other.featured_entities)
        self.primary_inactive_color.update(other.primary_inactive_color)
        self.primary_active_color.update(other.primary_active_color)
        self.link_inactive_color.update(other.link_inactive_color)
        self.link_active_color.update(other.link_active_color)
        self.logo = other.logo

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("featured_entities", self.featured_entities.load),
            OptionalField("primary_inactive_color", self.primary_inactive_color.load),
            OptionalField("primary_active_color", self.primary_active_color.load),
            OptionalField("link_inactive_color", self.link_inactive_color.load),
            OptionalField("link_active_color", self.link_active_color.load),
            OptionalField("logo", assert_path() | assert_setattr(self, "logo")),
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            {
                "featured_entities": self.featured_entities.dump(),
                "primary_inactive_color": self._primary_inactive_color.dump(),
                "primary_active_color": self._primary_active_color.dump(),
                "link_inactive_color": self._link_inactive_color.dump(),
                "link_active_color": self._link_active_color.dump(),
                "logo": str(self._logo) if self._logo else Void,
            }
        )
