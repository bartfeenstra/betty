"""
Configuration for ordered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import TypeVar

from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object.property import SequenceProperty
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, ResolvableId, resolve_id
from betty.plugin.config import PluginDefinitionConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterable

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class OrderedPluginDefinitionConfiguration(
    PluginDefinitionConfiguration[_PluginDefinitionT]
):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.

    .. data:: betty.plugin.config.ordered:OrderedPluginDefinitionConfiguration
    """

    comes_before = SequenceProperty(
        SequenceDefinition(cls=list, label=_("Comes before"), value=MachineName),
        omit_load=True,
        omit_dump=lambda data: not len(data),
        default=list,
    )
    comes_after = SequenceProperty(
        SequenceDefinition(cls=list, label=_("Comes after"), value=MachineName),
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
        if comes_before is not None:
            self.comes_before = map(resolve_id, comes_before)
        if comes_after is not None:
            self.comes_after = map(resolve_id, comes_after)
