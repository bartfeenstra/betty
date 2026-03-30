"""
Plugin configuration properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.keyed.adapter import MutableKeyedCollectionAdapter
from betty.collection.sequence import (
    MutableResolvedSequence,
)
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.indicator.selector import Attr
from betty.plugin import PluginDefinition
from betty.plugin.cls import Plugin
from betty.plugin.data import PluginManufacturerSequenceDefinition
from betty.plugin.factory import (
    PluginManufacturer,
    ResolvablePluginManufacturer,
    ResolvablePluginManufacturerSequence,
)
from betty.property.collection.keyed import KeyedCollectionProperty
from betty.property.collection.sequence import SequenceProperty

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.plugin.data import PluginDefinitionConfiguration


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


@final
class PluginDefinitionConfigurationsProperty[PluginDefinitionT: PluginDefinition](
    KeyedCollectionProperty
):
    """
    A property containing a :py:class:`betty.collection.keyed.KeyedCollection` of :py:class:`betty.plugin.data.PluginDefinitionConfiguration`.
    """

    def __init__(
        self,
        plugin_type: type[PluginDefinitionT],
        item: type[PluginDefinitionConfiguration[PluginDefinitionT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            KeyedCollectionDefinition(
                value=item,
                label=plugin_type.type().label_plural,
                key=Attr("id"),
                factory=lambda: MutableKeyedCollectionAdapter(key=lambda item: item.id),
            ),
            label=label,
            description=description,
            omit_load=True,
            omit_dump=lambda data: not len(data),
        )
