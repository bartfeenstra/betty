"""
The classed plugin factory API.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Final, Self, final, override

from typing_extensions import disjoint_base

from betty.attrs.machine_name import new_machine_name_attr
from betty.classtools import TypeABCMeta
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.id import ResolvableId, resolve_id
from betty.factory import Manufacturable
from betty.freezer import Frozen
from betty.localizables.gettext import _
from betty.plugin.config import ConfigurablePluginDefinition
from betty.plugin.config.factory import (
    NewConfigurablePlugin,
    _NewConfigurablePluginPorter,
)
from betty.prop import HasProps
from betty.service_level.factory import Integratable, IntegratableFactory, Integrator
from betty.service_level.factory import new as service_level_new

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.service_level import ServiceLevel


type ManufacturablePlugin[PluginT] = (
    Intersection[PluginT, Manufacturable] | Intersection[PluginT, Callable[[], PluginT]]
)


type IntegratablePlugin[PluginT] = (
    Intersection[PluginT, Integratable] | ManufacturablePlugin[PluginT]
)


type PluginFactory[PluginT, NewPluginT: PluginManufacturer] = (
    NewPluginT | IntegratableFactory[PluginT]
)


async def new[PluginT, NewPluginT: NewPlugin](
    plugin: PluginFactory[PluginT, NewPluginT],
    services: ServiceLevel,
    /,
) -> PluginT:
    """
    Create a new plugin instance.
    """
    if isinstance(plugin, NewPlugin):
        return await plugin.new(services)
    return await service_level_new(plugin, services)


@disjoint_base
class PluginManufacturer[
    DefinitionT: ClassedPluginDefinition,
    PluginT,
    DataT: Data,
](DataT, HasProps, Frozen, Integrator[PluginT], metaclass=TypeABCMeta):
    """
    A plugin manufacturer.
    """

    id = new_machine_name_attr(label=_("ID"))
    """
    The plugin ID.
    """

    def __init__(self, plugin_id: ResolvableId[DefinitionT], /):
        super().__init__()
        self.id = resolve_id(plugin_id)

    @override
    def __hash__(self):
        return hash((type(self), self.id))

    @final
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return hash(self) == hash(other)

    @final
    @classmethod
    def resolve(cls, factory: PluginFactory[PluginT, Self]) -> Self:
        """
        Resolve a value to an instance of ``self``.
        """
        if isinstance(factory, cls):
            return factory
        return cls(resolve_id(factory))


# @todo We really don't need this to be a factory?
# @todo Plugins with dependencies (integration or config), those are not a thing for non-functional plugins.
# @todo All we need is a way to map string IDs to plugin ID machine names (which can be done when loading and dumping).
# @todo That means that for those plugins, this only ever needs to be a PODO.
# @todo That also means that we can use MachineName instead? Except that we want to upcast it to a plugin definition
# @todo (we don't inject machine names into services, we inject plugin definitions).
# @todo
# @todo
# @todo
# @todo
class NewPlugin[DefinitionT: ClassedPluginDefinition, PluginT](
    PluginManufacturer[
        DefinitionT,
        PluginT,
        Data["NewPluginDefinition[DefinitionT, PluginT]"],
    ]
):
    """
    Configure a single plugin instance.
    """

    @final
    @override
    def __hash__(self):
        return hash((type(self), self.data().plugin_type, self.id))

    @final
    @override
    async def new(self, services: ServiceLevel, /) -> PluginT:
        definition = await services.plugins[self.data().plugin_type][self.id]
        return await new(definition.cls, services)


@final
class NewPluginDefinition[
    DefinitionT: ConfigurablePluginDefinition,
    PluginT,
](ObjectDefinition[NewConfigurablePlugin[DefinitionT, PluginT]]):
    """
    Define a configurable plugin factory.
    """

    def __init__(self, plugin_type: type[DefinitionT], /):
        super().__init__(
            label=plugin_type.type().label,
            porter=lambda definition: _NewConfigurablePluginPorter(definition.cls),
        )
        self.plugin_type: Final[type[DefinitionT]] = plugin_type
