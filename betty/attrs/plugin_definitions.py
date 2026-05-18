"""
Plugin definition configurations properties.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, final

from betty.attr import ProxyAttr
from betty.attrs.collection_attr import CollectionAttrAttr
from betty.collection.keyed import MutableKeyedCollection
from betty.collection.keyed.adapter import MutableKeyedCollectionAdapter
from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.datas.plugin_definition import PluginDefinitionData
from betty.indicator.selector import Attr
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginId
from betty.property import HasProperties

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class PluginDefinitionDatasAttr[PluginDefinitionT: PluginDefinition](
    ProxyAttr[
        HasProperties,
        MutableKeyedCollection[
            MachineName,
            ResolvablePluginId[PluginDefinitionT],
            PluginDefinitionData[PluginDefinitionT],
            PluginDefinitionData[PluginDefinitionT],
        ],
        Iterable[PluginDefinitionData[PluginDefinitionT]],
    ]
):
    """
    An attribute containing a :py:class:`betty.collection.keyed.KeyedCollection` of :py:class:`betty.datas.plugin_definition.PluginDefinitionData`.
    """

    def __init__(
        self,
        plugin_type: type[PluginDefinitionT],
        item: type[PluginDefinitionData[PluginDefinitionT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            CollectionAttrAttr(
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
                    key=Attr("id"),
                    factory=lambda: MutableKeyedCollectionAdapter(
                        key=lambda item: item.id
                    ),
                ),
                label=label,
                description=description,
                omit_load=True,
                omit_dump=lambda data: not len(data),
            )
        )
