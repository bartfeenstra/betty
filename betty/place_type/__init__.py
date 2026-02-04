"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.service.requirement.project import require_project


class PlaceType(Plugin["PlaceTypeDefinition"]):
    """
    Define a :py:class:`betty.ancestry.place.Place` type.
    """


@final
@PluginTypeDefinition(
    "place-type",
    label=_("Place type"),
    label_plural=_("Place types"),
    label_countable=ngettext("{count} place type", "{count} place types"),
    discovery=[
        EntryPointDiscovery("betty.place_type"),
        require_project(
            lambda project: (
                configuration.new_plugin()
                for configuration in project.configuration.place_types
            )
        ),
    ],
)
class PlaceTypeDefinition(CountableHumanFacingDefinition, PluginDefinition[PlaceType]):
    """
    .. plugin_type:: place-type.
    """
