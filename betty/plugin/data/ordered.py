"""
Configuration for ordered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, ResolvablePluginId, resolve_plugin_id
from betty.plugin.data import PluginDefinitionConfiguration
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

    comes_before = SequenceProperty(
        SequenceDefinition(cls=list, label=_("Comes before"), value=MachineName),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    comes_after = SequenceProperty(
        SequenceDefinition(cls=list, label=_("Comes after"), value=MachineName),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )

    def __init__(
        self,
        comes_before: Iterable[ResolvablePluginId] | None = None,
        comes_after: Iterable[ResolvablePluginId] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if comes_before is not None:
            self.comes_before = map(resolve_plugin_id, comes_before)
        if comes_after is not None:
            self.comes_after = map(resolve_plugin_id, comes_after)
