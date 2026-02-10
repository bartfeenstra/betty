"""
Provide plugin configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from betty.data import Data
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import (
    CountableLocalizableProperty,
    LocalizableProperty,
)
from betty.machine_name import MachineNameProperty, ResolvableMachineName
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import (
        ResolvableCountableLocalizable,
        ResolvableLocalizable,
    )


class PluginDefinitionConfiguration[
    PluginDefinitionT: PluginDefinition = PluginDefinition
](Data[ObjectDefinition["PluginDefinitionConfiguration"]], ABC):
    """
    Configure a :py:class:`betty.plugin.PluginDefinition`.

    .. data:: betty.plugin.config:PluginDefinitionConfiguration
    """

    id = MachineNameProperty(label=_("Plugin ID"))
    """
    The plugin ID.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName,  # noqa: A002
    ):
        super().__init__()
        self.id = id

    @abstractmethod
    def new_plugin(self) -> PluginDefinitionT:
        """
        Create a new plugin from this configuration.
        """


class HumanFacingPluginDefinitionConfiguration[
    PluginDefinitionT: PluginDefinition = PluginDefinition
](PluginDefinitionConfiguration[PluginDefinitionT]):
    """
    Configure a :py:class:`betty.definition.human_facing.HumanFacingDefinition`.

    .. data:: betty.plugin.config:HumanFacingPluginDefinitionConfiguration
    """

    label = LocalizableProperty(label=_("Label"))
    description = Optional(LocalizableProperty(label=_("Description")))

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


class CountableHumanFacingPluginDefinitionConfiguration[
    PluginDefinitionT: PluginDefinition = PluginDefinition
](HumanFacingPluginDefinitionConfiguration[PluginDefinitionT]):
    """
    Configure a :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition`.

    .. data:: betty.plugin.config:CountableHumanFacingPluginDefinitionConfiguration
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
