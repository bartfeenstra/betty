"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer

if TYPE_CHECKING:
    import builtins


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
)
class PlaceTypeDefinition(CountableHumanFacingDefinition, PluginDefinition[PlaceType]):
    """
    .. plugin_type:: place-type.
    """


@final
class PlaceTypeManufacturer(PluginManufacturer[PlaceTypeDefinition, PlaceType]):
    """
    The place type manufacturer.
    """

    @override
    @classmethod
    def type(cls) -> builtins.type[PlaceTypeDefinition]:
        return PlaceTypeDefinition
