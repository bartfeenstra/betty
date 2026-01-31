"""
Plugin configuration properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar

from betty.collections import KeyedCollection, ResolvingMutableSequence
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.record.object.property import (
    KeyedCollectionProperty,
    SequenceProperty,
)
from betty.data.indicator.selector import Attr
from betty.plugin import Plugin, PluginClsDefinition, PluginDefinition
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
_PluginClsDefinitionT = TypeVar(
    "_PluginClsDefinitionT", bound=PluginClsDefinition, default=PluginClsDefinition
)


@final
class PluginConfigurationSequenceProperty(
    SequenceProperty[
        ResolvingMutableSequence[
            PluginConfiguration[_PluginClsDefinitionT, _PluginT],
            ResolvablePluginConfiguration[_PluginClsDefinitionT, _PluginT],
        ],
        ResolvablePluginConfigurationSequence[_PluginClsDefinitionT, _PluginT],
    ]
):
    """
    A property containing a sequence of :py:class:`betty.plugin.config.PluginConfiguration`.
    """

    def __init__(
        self,
        plugin_type: type[_PluginClsDefinitionT],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            PluginConfigurationSequenceDefinition(plugin_type),
            label=label,
            description=description,
            resolver=resolve_plugin_configuration_sequence,
            default=lambda: ResolvingMutableSequence([], resolve_plugin_configuration),
        )


@final
class PluginDefinitionConfigurationsProperty(KeyedCollectionProperty):
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
            KeyedCollectionDefinition(
                value=item,
                label=plugin_type.type().label_plural,
                key=Attr("id"),
                ordered=False,
            ),  # ty:ignore[invalid-argument-type]
            label=label,
            description=description,
            omit_load=True,
            omit_dump=lambda data: not len(data),
            default=lambda: KeyedCollection(key=lambda item: item.id),
        )
