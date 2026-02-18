"""
Plugin configuration properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collections import (
    MutableDictKeyedCollection,
    MutableResolvedSequence,
    MutableResolvedSequenceProxy,
)
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.record.object.property import (
    KeyedCollectionProperty,
    SequenceProperty,
)
from betty.data.indicator.selector import Attr
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.data import PluginManufacturerSequenceDefinition
from betty.plugin.factory import (
    PluginManufacturer,
    ResolvablePluginManufacturer,
    ResolvablePluginManufacturerSequence,
)

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
            default=lambda: MutableResolvedSequenceProxy(
                [], value_resolver=manufacturer.resolve
            ),
        )


@final
class PluginDefinitionConfigurationsProperty[PluginDefinitionT: PluginDefinition](
    KeyedCollectionProperty
):
    """
    A property containing a :py:class:`betty.collections.KeyedCollection` of :py:class:`betty.plugin.data.PluginDefinitionConfiguration`.
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
                ordered=False,
            ),
            label=label,
            description=description,
            omit_load=True,
            omit_dump=lambda data: not len(data),
            default=lambda: MutableDictKeyedCollection(key=lambda item: item.id),
        )
