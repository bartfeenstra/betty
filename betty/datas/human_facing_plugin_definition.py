"""
Human-facing plugin definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.localizable import new_localizable_attr
from betty.attrs.optional import Optional
from betty.datas.plugin_definition import PluginDefinitionData
from betty.locale.localizable.gettext import _
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


class HumanFacingPluginDefinitionData[
    PluginDefinitionT: PluginDefinition = PluginDefinition
](PluginDefinitionData[PluginDefinitionT]):
    """
    Configure a :py:class:`betty.definition.human_facing.HumanFacingDefinition`.

    .. data:: betty.datas.human_facing_plugin_definition:HumanFacingPluginDefinitionData
    """

    label = new_localizable_attr(label=_("Label"))
    description = Optional(new_localizable_attr(label=_("Description")))

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label = label
        self.description = description
