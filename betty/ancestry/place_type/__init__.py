"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.data import Data
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.data import DataPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import (
    CountableHumanFacingPluginDefinition,
)


class PlaceType(Data, Plugin["PlaceTypeDefinition"]):
    """
    Define a :py:class:`betty.ancestry.place.Place` type.
    """


@final
@PluginTypeDefinition(
    "place-type",
    base_cls=PlaceType,
    label=_("Place type"),
    label_plural=_("Place types"),
    label_countable=ngettext("{count} place type", "{count} place types"),
    discovery=[
        EntryPointDiscovery("betty.place_type"),
        ProjectDiscovery(
            lambda project: project.configuration.place_types.new_plugins(),
        ),
    ],
)
class PlaceTypeDefinition(
    CountableHumanFacingPluginDefinition[PlaceType], DataPluginDefinition[PlaceType]
):
    """
    .. plugin_type:: place-type.
    """
