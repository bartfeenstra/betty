"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition


class PlaceType(Plugin):
    """
    Define an :py:class:`betty.ancestry.place.Place` type.

    Read more about :doc:`/development/plugin/place-type`.
    """

    plugin: ClassVar[PlaceTypeDefinition]


@final
class PlaceTypeDefinition(HumanFacingPluginDefinition[PlaceType]):
    """
    A place type definition.

    Read more about :doc:`/development/plugin/place-type`.
    """

    type = PluginTypeDefinition(
        "place-type",
        PlaceType,
        _("Place type"),
        discoveries=[
            EntryPointDiscovery("betty.place_type"),
            ProjectDiscovery(
                lambda project: project.configuration.place_types.new_plugins(),
            ),
        ],
    )
