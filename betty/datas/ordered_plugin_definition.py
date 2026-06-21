"""
Ordered plugin definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.owner import CollectionOwnerAttr
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.plugin_definition import PluginDefinitionData
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.plugin.ordered import OrderedPluginDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id

if TYPE_CHECKING:
    from collections.abc import Iterable


class OrderedPluginDefinitionData[PluginDefinitionT: OrderedPluginDefinition](
    PluginDefinitionData[PluginDefinitionT]
):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.

    .. data:: betty.datas.ordered_plugin_definition:OrderedPluginDefinitionData
    """

    after = CollectionOwnerAttr(
        SequenceDefinition(cls=list, label=_("After"), value=MachineName),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    before = CollectionOwnerAttr(
        SequenceDefinition(cls=list, label=_("Before"), value=MachineName),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )

    def __init__(
        self,
        after: Iterable[ResolvablePluginId] = (),
        before: Iterable[ResolvablePluginId] = (),
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.after = map(resolve_plugin_id, after)
        self.before = map(resolve_plugin_id, before)
