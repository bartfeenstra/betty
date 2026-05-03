"""
Plugin definition configurations properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.keyed.adapter import MutableKeyedCollectionAdapter
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.indicator.selector import Attr
from betty.plugin import PluginDefinition
from betty.properties.collection.keyed import KeyedCollectionProperty

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.plugin.data import PluginDefinitionConfiguration


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
