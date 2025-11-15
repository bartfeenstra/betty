"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
    ProjectPluginRepositoryDefinition,
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

    plugin_type_cls = PlaceType
    repository = ProjectPluginRepositoryDefinition(
        lambda project: project.place_type_repository
    )
    type = PluginTypeDefinition(
        id="place-type",
        label=_("Place type"),
    )
