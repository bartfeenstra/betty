"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class PlaceType(Plugin["PlaceTypeDefinition"]):
    """
    Define a :py:class:`betty.plugins.entity.place.Place` type.
    """


@final
@PluginTypeDefinition(
    "place-type",
    label=_("Place type"),
    label_plural=_("Place types"),
    label_countable=ngettext("{count} place type", "{count} place types"),
)
class PlaceTypeDefinition(
    CountableHumanFacingDefinition, PluginClsDefinition[PlaceType]
):
    """
    .. plugin_type:: place-type.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            requires=requires,
        )


@final
@PluginManufacturerDefinition(PlaceTypeDefinition)
class PlaceTypeManufacturer(PluginManufacturer[PlaceTypeDefinition, PlaceType]):
    """
    The place type manufacturer.
    """
