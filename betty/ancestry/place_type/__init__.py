"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, final

from betty.locale.localizable import _
from betty.mutability import Mutable
from betty.plugin import (
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    UserFacingPluginDefinition,
)
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.plugin import PluginRepository


class PlaceType(Mutable):
    """
    Define an :py:class:`betty.ancestry.place.Place` type.

    Read more about :doc:`/development/plugin/place-type`.
    """

    plugin: ClassVar[PlaceTypeDefinition]


@final
class PlaceTypeDefinition(
    UserFacingPluginDefinition, ClassedPluginDefinition[PlaceType]
):
    """
    A place type definition.

    Read more about :doc:`/development/plugin/place-type`.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="place-type",
        label=_("Place type"),
        cls=PlaceType,
    )


PLACE_TYPE_REPOSITORY: PluginRepository[PlaceTypeDefinition] = (
    EntryPointPluginRepository(PlaceTypeDefinition, "betty.place_type")
)
"""
The place type plugin repository.

Read more about :doc:`/development/plugin/place-type`.
"""
