"""
Plugin configuration properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar

from betty.collections import (
    MutableResolvedSequence,
    MutableResolvedSequenceProxy,
    PrimaryKeyMapping,
)
from betty.data.aggregate.collection.mapping import AutoMappingDefinition
from betty.data.aggregate.record.object.property import (
    AutoMappingProperty,
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

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class PluginConfigurationSequenceProperty(
    SequenceProperty[
        MutableResolvedSequence[
            PluginConfiguration[_PluginDefinitionT, _PluginT],
            ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT],
        ],
        ResolvablePluginConfigurationSequence[_PluginDefinitionT, _PluginT],
    ]
):
    """
    A property containing a sequence of :py:class:`betty.plugin.config.PluginConfiguration`.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
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
class PluginDefinitionConfigurationsProperty(AutoMappingProperty):
    """
    A property containing a :py:class:`betty.collections.KeyedCollection` of :py:class:`betty.plugin.config.PluginDefinitionConfiguration`.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
        item: type[PluginDefinitionConfiguration[_PluginDefinitionT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            AutoMappingDefinition(
                value=item,
                label=plugin_type.type().label_plural,
                key=Attr("id"),
                ordered=False,
            ),
            label=label,
            description=description,
            omit_load=True,
            omit_dump=lambda data: not len(data),
            default=lambda: PrimaryKeyMapping(key=lambda item: item.id),
        )
