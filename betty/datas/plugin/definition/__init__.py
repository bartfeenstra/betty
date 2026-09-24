"""
Reusable data for plugin definitions.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self, final

from betty.attrs.machine_name import new_machine_name_attr
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition import resolve_definition
from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.porters.fields import FieldsPorter
from betty.porters.keyed_mapping import KeyedMappingPorter

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import ResolvableDataSamples
    from betty.definition import ResolvableDefinition
    from betty.machine_name import ResolvableMachineName


@final
class PluginDefinitionDefinition[
    DefinitionT: Intersection[PluginDefinition, HumanFacingDefinition]
](ObjectDefinition["PluginDefinitionData[DefinitionT]"]):
    """
    Define a plugin definition.
    """

    def __init__(
        self,
        plugin_type: ResolvableDefinition[PluginTypeDefinition[DefinitionT]],
        /,
        *,
        samples: ResolvableDataSamples[Self, PluginDefinitionData[DefinitionT]]
        | None = None,
    ):
        plugin_type = resolve_definition(plugin_type)
        super().__init__(
            label=_("{plugin_type} configuration").format(
                plugin_type=plugin_type.label
            ),
            porter=lambda definition: KeyedMappingPorter(
                "id", FieldsPorter(definition)
            ),
            samples=samples,
        )


class PluginDefinitionData[
    DefinitionT: Intersection[PluginDefinition, HumanFacingDefinition]
](Object[PluginDefinitionDefinition[DefinitionT]]):
    """
    Configure a :py:class:`betty.plugin.PluginDefinition`.

    .. data:: betty.datas.plugin_definition:PluginDefinitionData
    """

    id = new_machine_name_attr(label=_("Plugin ID"))
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
    def new_plugin(self) -> DefinitionT:
        """
        Create a new plugin from this configuration.
        """
