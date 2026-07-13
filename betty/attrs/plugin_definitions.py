"""
Plugin definition configurations attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import CollectionOwnerAttr
from betty.collection.keyed import MutableKeyedCollection
from betty.collections.keyed.adapter import MutableKeyedCollectionAdapter
from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.plugin.definition import PluginDefinitionData
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginId

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.attrs.common import CommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.prop import HasProps


def new_plugin_definition_datas_attr[PluginDefinitionT: PluginDefinition](
    plugin_type: type[PluginDefinitionT],
    item: type[PluginDefinitionData[PluginDefinitionT]],
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[
    HasProps,
    MutableKeyedCollection[
        MachineName,
        ResolvablePluginId[PluginDefinitionT],
        PluginDefinitionData[PluginDefinitionT],
        PluginDefinitionData[PluginDefinitionT],
    ],
    Iterable[PluginDefinitionData[PluginDefinitionT]],
]:
    """
    Create attribute containing a :py:class:`betty.collection.keyed.KeyedCollection` of :py:class:`betty.datas.plugin.definition.PluginDefinitionData`.
    """
    return CollectionOwnerAttr(
        FieldDefinition(
            KeyedCollectionDefinition[
                MutableKeyedCollection[
                    MachineName,
                    ResolvablePluginId[PluginDefinitionT],
                    PluginDefinitionData[PluginDefinitionT],
                    PluginDefinitionData[PluginDefinitionT],
                ],
                PluginDefinitionData[PluginDefinitionT],
            ](
                value=item,
                label=plugin_type.type().label_plural,
                factory=lambda: MutableKeyedCollectionAdapter(key=lambda item: item.id),
            ),
            label=label,
            description=description,
            omit_load=True,
            omit_dump=lambda data: not len(data),
        )
    )
