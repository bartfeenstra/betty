"""
Provide configuration for the Raspberry Mint extension.
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


class RaspberryMintConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.project.extension.raspberry_mint.RaspberryMint` extension.
    """

    DEFAULT_PRIMARY_COLOR = "#b3446c"
    DEFAULT_SECONDARY_COLOR = "#3eb489"
    DEFAULT_TERTIARY_COLOR = "#ffbd22"

    def __init__(
        self,
        *,
        featured_entities: (
            Sequence[EntityReference[UserFacingEntity & Entity]] | None
        ) = None,
        primary_color: str = DEFAULT_PRIMARY_COLOR,
        secondary_color: str = DEFAULT_SECONDARY_COLOR,
        tertiary_color: str = DEFAULT_TERTIARY_COLOR,
    ):
        super().__init__()
        self._featured_entities = EntityReferenceSequence["UserFacingEntity & Entity"](
            featured_entities or ()
        )
        self._primary_color = ColorConfiguration(primary_color)
        self._secondary_color = ColorConfiguration(secondary_color)
        self._tertiary_color = ColorConfiguration(tertiary_color)

    @override
    def get_mutable_instances(self) -> Iterable[Mutable]:
        return (
            self._featured_entities,
            self._primary_color,
            self._secondary_color,
            self._tertiary_color,
        )

    @property
    def featured_entities(self) -> EntityReferenceSequence[UserFacingEntity & Entity]:
        """
        The entities featured on the front page.
        """
        return self._featured_entities

    @property
    def primary_color(self) -> ColorConfiguration:
        """
        The primary color.
        """
        return self._primary_color

    @property
    def secondary_color(self) -> ColorConfiguration:
        """
        The secondary color.
        """
        return self._secondary_color

    @property
    def tertiary_color(self) -> ColorConfiguration:
        """
        The tertiary color.
        """
        return self._tertiary_color

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField("featured_entities", self.featured_entities.load),
            OptionalField("primary_color", self.primary_color.load),
            OptionalField("secondary_color", self.secondary_color.load),
            OptionalField("tertiary_color", self.tertiary_color.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "featured_entities": self.featured_entities.dump(),
            "primary_color": self.primary_color.dump(),
            "secondary_color": self.secondary_color.dump(),
            "tertiary_color": self.tertiary_color.dump(),
        }
