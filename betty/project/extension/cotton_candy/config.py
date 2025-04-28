"""
Provide configuration for the Cotton Candy extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.assertion import OptionalField, assert_record
from betty.config import Configuration
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.project.extension._theme import ColorConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.model import Entity, UserFacingEntity
    from betty.mutability import Mutable
    from betty.serde.dump import Dump, DumpMapping


class CottonCandyConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.project.extension.cotton_candy.CottonCandy` extension.
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
    ):
        super().__init__()
        self._featured_entities = EntityReferenceSequence["UserFacingEntity & Entity"](
            featured_entities or ()
        )
        self._primary_inactive_color = ColorConfiguration(primary_inactive_color)
        self._primary_active_color = ColorConfiguration(primary_active_color)
        self._link_inactive_color = ColorConfiguration(link_inactive_color)
        self._link_active_color = ColorConfiguration(link_active_color)

    @override
    def get_mutable_instances(self) -> Iterable[Mutable]:
        return (
            self._featured_entities,
            self._primary_active_color,
            self._primary_inactive_color,
            self._link_active_color,
            self._link_inactive_color,
        )

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

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField("featured_entities", self.featured_entities.load),
            OptionalField("primary_inactive_color", self.primary_inactive_color.load),
            OptionalField("primary_active_color", self.primary_active_color.load),
            OptionalField("link_inactive_color", self.link_inactive_color.load),
            OptionalField("link_active_color", self.link_active_color.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "featured_entities": self.featured_entities.dump(),
            "primary_inactive_color": self._primary_inactive_color.dump(),
            "primary_active_color": self._primary_active_color.dump(),
            "link_inactive_color": self._link_inactive_color.dump(),
            "link_active_color": self._link_active_color.dump(),
        }
