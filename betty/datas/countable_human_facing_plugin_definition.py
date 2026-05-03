"""
Countable human-facing plugin definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.datas.human_facing_plugin_definition import (
    HumanFacingPluginDefinitionData,
)
from betty.locale.localizable.gettext import _
from betty.plugin import PluginDefinition
from betty.properties.countable_localizable import CountableLocalizableProperty
from betty.properties.localizable import LocalizableProperty

if TYPE_CHECKING:
    from betty.locale.localizable import (
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

    label_plural = LocalizableProperty(label=_("Label (plural)"))
    label_countable = CountableLocalizableProperty(label=_("Label (countable)"))

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
