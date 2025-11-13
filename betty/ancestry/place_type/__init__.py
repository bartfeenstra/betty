"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    HumanFacingPluginDefinition,
)


class PlaceType(ClassedPlugin):
    """
    Define an :py:class:`betty.ancestry.place.Place` type.

    Read more about :doc:`/development/plugin/place-type`.
    """

    plugin: ClassVar[PlaceTypeDefinition]


@final
class PlaceTypeDefinition(
    HumanFacingPluginDefinition, ClassedPluginDefinition[PlaceType]
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
