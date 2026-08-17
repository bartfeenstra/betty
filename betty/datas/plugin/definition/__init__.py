"""
Reusable data for plugin definitions.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from betty.attrs.machine_name import new_machine_name_attr
from betty.classtools import InitABCMeta
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.cls import OnSetCls
from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _
from betty.plugin import PluginDefinition
from betty.plugin.resolve import (
    resolve_plugin_type_definition,
)
from betty.portable import KeyedPorter
from betty.porters.fields import FieldsPorter
from betty.porters.keyed_mapping import KeyedMappingPorter
from betty.prop import HasProps
from betty.typing import Intersection

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from betty.machine_name import ResolvableMachineName
    from betty.plugin.resolve import ResolvablePluginTypeDefinition
    from betty.sample import Sample, Samples


@final
class PluginDefinitionDefinition[
    PluginDefinitionT: Intersection[PluginDefinition, HumanFacingDefinition],
    PluginDefinitionDataT: "PluginDefinitionData",
](
    ObjectDefinition[
        Intersection[PluginDefinitionDataT, "PluginDefinitionData[PluginDefinitionT]"],
        KeyedPorter[
            Intersection[
                PluginDefinitionDataT, "PluginDefinitionData[PluginDefinitionT]"
            ]
        ],
    ]
):
    """
    Define a plugin definition.
    """

    def __init__(
        self,
        plugin_type: ResolvablePluginTypeDefinition[PluginDefinitionT],
        /,
        *,
        samples: Iterable[Callable[[], Sample[PluginDefinitionDataT]] | Samples] = (),
    ):
        plugin_type = resolve_plugin_type_definition(plugin_type)
        super().__init__(
            label=_("{plugin_type} configuration").format(
                plugin_type=plugin_type.label
            ),
            porter=OnSetCls(
                lambda definition: KeyedMappingPorter("id", FieldsPorter(definition))
            ),
            samples=samples,
        )


class PluginDefinitionData[
    PluginDefinitionT: PluginDefinition = Intersection[
        PluginDefinition, HumanFacingDefinition
    ]
](
    Data[PluginDefinitionDefinition[PluginDefinitionT, "PluginDefinitionData"]],
    HasProps,
    metaclass=InitABCMeta,
):
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
    def new_plugin(self) -> PluginDefinitionT:
        """
        Create a new plugin from this configuration.
        """
