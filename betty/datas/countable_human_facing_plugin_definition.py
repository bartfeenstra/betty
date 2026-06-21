"""
Countable human-facing plugin definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.countable_localizable import new_countable_localizable_attr
from betty.attrs.localizable import new_localizable_attr
from betty.datas.human_facing_plugin_definition import (
    HumanFacingPluginDefinitionData,
)
from betty.localizables.gettext import _
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from betty.localizable import (
        ResolvableCountableLocalizable,
        ResolvableLocalizable,
    )


class CountableHumanFacingPluginDefinitionData[
    PluginDefinitionT: PluginDefinition = PluginDefinition
](HumanFacingPluginDefinitionData[PluginDefinitionT]):
    """
    Configure a :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition`.

    .. data:: betty.datas.countable_human_facing_plugin_definition:CountableHumanFacingPluginDefinitionData
    """

    label_plural = new_localizable_attr(label=_("Label (plural)"))
    label_countable = new_countable_localizable_attr(label=_("Label (countable)"))

    def __init__(
        self,
        *,
        label_plural: ResolvableLocalizable,
        label_countable: ResolvableCountableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label_plural = label_plural
        self.label_countable = label_countable
