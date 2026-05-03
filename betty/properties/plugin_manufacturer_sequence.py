"""
Plugin manufacturer sequence properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.sequence import MutableResolvedSequence
from betty.datas.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.plugin import PluginDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import (
    PluginManufacturer,
    ResolvablePluginManufacturer,
    ResolvablePluginManufacturerSequence,
)
from betty.properties.collection.sequence import SequenceProperty

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class PluginManufacturerSequenceProperty[
    PluginDefinitionT: PluginDefinition,
    PluginT: Plugin,
](
    SequenceProperty[
        MutableResolvedSequence[
            PluginManufacturer[PluginDefinitionT, PluginT],
            ResolvablePluginManufacturer[PluginDefinitionT, PluginT],
        ],
        PluginManufacturer[PluginDefinitionT, PluginT],
        ResolvablePluginManufacturerSequence[PluginDefinitionT, PluginT],
    ]
):
    """
    A property containing a sequence of :py:class:`betty.plugin.factory.PluginManufacturer`.
    """

    def __init__(
        self,
        manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            PluginManufacturerSequenceDefinition(manufacturer),
            label=label,
            description=description,
            resolver=manufacturer.resolve_sequence,
        )
