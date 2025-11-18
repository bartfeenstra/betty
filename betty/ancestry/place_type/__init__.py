"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    GlobalPluginRepositoryDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
    ProjectPluginRepositoryDefinition,
)
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.plugin.static import StaticPluginRepository


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
    type = PluginTypeDefinition(
        id="place-type",
        label=_("Place type"),
        repositories=(
            GlobalPluginRepositoryDefinition(
                lambda: EntryPointPluginRepository(
                    PlaceTypeDefinition, "betty.place_type"
                )
            ),
            ProjectPluginRepositoryDefinition(
                lambda project: StaticPluginRepository(
                    PlaceTypeDefinition,
                    *project.configuration.place_types.new_plugins(),
                )
            ),
        ),
    )
