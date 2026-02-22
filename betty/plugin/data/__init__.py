"""
Data types for plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, final

from betty.collection.sequence import (
    MutableResolvedSequence,
)
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.data import Data
from betty.data.aggregate.collection.sequence import SequenceDefinition
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
    from betty.plugin.factory import PluginManufacturer


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


@final
class PluginManufacturerSequenceDefinition(SequenceDefinition):
    """
    Define a sequence of plugin instance configurations.
    """

    def __init__(
        self,
        manufacturer: type[PluginManufacturer],
        *,
        label: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=MutableResolvedSequence,
            factory=lambda: MutableResolvedSequenceAdapter(
                [], value_resolver=manufacturer.resolve
            ),
            value=manufacturer,
            label=manufacturer.type().type().label_plural if label is None else label,
        )
