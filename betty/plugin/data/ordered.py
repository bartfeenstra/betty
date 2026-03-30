"""
Configuration for ordered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.data import PluginDefinitionConfiguration
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.property.collection.sequence import SequenceProperty

if TYPE_CHECKING:
    from collections.abc import Iterable


class OrderedPluginDefinitionConfiguration[PluginDefinitionT: PluginDefinition](
    PluginDefinitionConfiguration[PluginDefinitionT]
):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.

    .. data:: betty.plugin.config.ordered:OrderedPluginDefinitionConfiguration
    """

    after = SequenceProperty(
        SequenceDefinition(cls=list, label=_("After"), value=MachineName),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    before = SequenceProperty(
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
