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
from betty.plugin.config import (
    PluginConfiguration,
    PluginDefinitionConfiguration,
    ResolvablePluginConfiguration,
    ResolvablePluginConfigurationSequence,
    resolve_plugin_configuration,
    resolve_plugin_configuration_sequence,
)
from betty.plugin.data import PluginConfigurationSequenceDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class PluginConfigurationSequenceProperty[
    PluginDefinitionT: PluginDefinition,
    PluginT: Plugin,
](
    SequenceProperty[
        MutableResolvedSequence[
            PluginConfiguration[PluginDefinitionT, PluginT],
            ResolvablePluginConfiguration[PluginDefinitionT, PluginT],
        ],
        ResolvablePluginConfigurationSequence[PluginDefinitionT, PluginT],
    ]
):
    """
    A property containing a sequence of :py:class:`betty.plugin.config.PluginConfiguration`.
    """

    def __init__(
        self,
        plugin_type: type[PluginDefinitionT],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            PluginConfigurationSequenceDefinition(plugin_type),
            label=label,
            description=description,
            resolver=resolve_plugin_configuration_sequence,
            default=lambda: MutableResolvedSequenceProxy(
                [], value_resolver=resolve_plugin_configuration
            ),
        )


@final
class PluginDefinitionConfigurationsProperty[PluginDefinitionT: PluginDefinition](
    KeyedCollectionProperty
):
    """
    A property containing a :py:class:`betty.collections.KeyedCollection` of :py:class:`betty.plugin.config.PluginDefinitionConfiguration`.
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
