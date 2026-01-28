"""
Configuration for ordered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object.property import Property
from betty.locale.localizable.gettext import _
from betty.plugin.config import PluginDefinitionConfiguration
from betty.plugin.data import PluginIdDefinition
from betty.plugin.resolve import resolve_id

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.resolve import ResolvableId


class OrderedPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.

    .. data:: betty.plugin.config.ordered:OrderedPluginDefinitionConfiguration
    """

    comes_before = Property(
        SequenceDefinition(
            cls=list, label=_("Comes before"), item=PluginIdDefinition()
        ),
        omit_load=True,
        omit_dump=lambda data: not len(data),
        default=list,
    )
    comes_after = Property(
        SequenceDefinition(cls=list, label=_("Comes after"), item=PluginIdDefinition()),
        omit_load=True,
        omit_dump=lambda data: not len(data),
        default=list,
    )

    def __init__(
        self,
        comes_before: Iterable[ResolvableId] | None = None,
        comes_after: Iterable[ResolvableId] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if comes_before:
            self.comes_before.extend(map(resolve_id, comes_before))
        if comes_after:
            self.comes_after.extend(map(resolve_id, comes_after))
