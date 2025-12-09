"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import (
    CountableHumanFacingPluginDefinition,
)


class PlaceType(Plugin["PlaceTypeDefinition"]):
    """
    Define an :py:class:`betty.ancestry.place.Place` type.

    Read more about :doc:`/development/plugin/place-type`.
    """


@final
@PluginTypeDefinition(
    "place-type",
    PlaceType,
    _("Place type"),
    _("Place types"),
    ngettext("{count} place type", "{count} place types"),
    discovery=[
        EntryPointDiscovery("betty.place_type"),
        ProjectDiscovery(
            lambda project: project.configuration.place_types.new_plugins(),
        ),
    ],
)
class PlaceTypeDefinition(CountableHumanFacingPluginDefinition[PlaceType]):
    """
    A place type definition.

    Read more about :doc:`/development/plugin/place-type`.
    """
