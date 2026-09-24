"""
The classed plugin factory API.
"""

from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING, final, overload, override

from typing_extensions import sentinel

from betty.attrs.owner import OwnerAttr
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.localizables.gettext import _
from betty.plugin.cls.factory import PluginManufacturer
from betty.plugin.config.factory import _NewConfigurablePluginPorter
from betty.portable import PortableData

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.definition import ResolvableDefinition
    from betty.definition.id import ResolvableId
    from betty.machine_name import ResolvableMachineName
    from betty.plugin.cls import ClassedPluginDefinition
    from betty.service_level import ServiceLevel

NoData = sentinel("NoData")


class NewDataPlugin[
    DefinitionT: Intersection[ClassedPluginDefinition, ObjectDefinition],
    PluginT,
](PluginManufacturer[DefinitionT, PluginT]):
    """
    Create new data plugin instances.
    """

    data = OwnerAttr(DataDefinition[Data | PortableData | NoData](label=_("Data")))
    """
    The plugin data.
    """

    @overload
    def __init__(self, plugin_id: ResolvableId[DefinitionT], /):
        pass

    @overload
    def __init__(
        self,
        plugin_id: ResolvableDefinition[DefinitionT],
        plugin_data: Data,
        /,
    ):
        pass

    @overload
    def __init__(self, plugin_id: ResolvableMachineName, plugin_data: PortableData, /):
        pass

    @final
    def __init__(self, plugin_id, plugin_data=NoData, /):
        super().__init__(plugin_id)
        self.data = plugin_data

    @final
    @override
    def __hash__(self):
        return hash((
            self.definition.plugin_type,
            self.id,
            NoData
            if self.data is NoData
            # @todo Finish the porter
            else dumps(_NewConfigurablePluginPorter.dump_config(self.data)),
        ))

    @final
    @override
    async def _new(self, services: ServiceLevel, plugin: DefinitionT, /) -> PluginT:
        # @todo Finish this
        raise NotImplementedError
