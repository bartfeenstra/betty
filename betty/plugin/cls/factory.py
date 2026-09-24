"""
The classed plugin factory API.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Final, Self, final, override

from typing_extensions import disjoint_base

from betty.attrs.machine_name import new_machine_name_attr
from betty.classtools import TypeABCMeta
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition.id import ResolvableId, resolve_id
from betty.factory import Manufacturable, new
from betty.freezer import Frozen
from betty.localizables.gettext import _
from betty.plugin.config import ConfigurablePluginDefinition
from betty.plugin.config.factory import (
    _NewConfigurablePluginPorter,
)
from betty.service_level.factory import Integrator

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.plugin.cls import ClassedPluginDefinition
    from betty.service_level import ServiceLevel


type ManufacturablePlugin[PluginT] = (
    Intersection[PluginT, Manufacturable] | Intersection[PluginT, Callable[[], PluginT]]
)


type PluginFactory[PluginT, NewPluginT: PluginManufacturer] = (
    NewPluginT | ManufacturablePlugin[PluginT]
)


@disjoint_base
class PluginManufacturer[
    DefinitionT: Intersection[ClassedPluginDefinition, ObjectDefinition],
    PluginT,
](
    Object["PluginManufacturerDefinition[DefinitionT, PluginT]"],
    Frozen,
    Integrator[PluginT],
    metaclass=TypeABCMeta,
):
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

    @abstractmethod
    def __hash__(self):
        pass

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

    @final
    @override
    async def new(self, services: ServiceLevel, /) -> PluginT:
        return await self._new(
            services, await services.plugins[self.definition.plugin_type][self.id]
        )

    @abstractmethod
    async def _new(self, services: ServiceLevel, plugin: DefinitionT, /) -> PluginT:
        pass


class PluginManufacturerDefinition[
    DefinitionT: ConfigurablePluginDefinition,
    PluginT,
](ObjectDefinition[PluginManufacturer[DefinitionT, PluginT]]):
    """
    Define a plugin manufacturer.
    """

    def __init__(self, plugin_type: type[DefinitionT], /):
        super().__init__(
            label=plugin_type.type().label,
            # @todo We cannot reuse the same porter for all PluginManufacturer subclasses
            porter=lambda definition: _NewConfigurablePluginPorter(definition.cls),
        )
        self.plugin_type: Final[type[DefinitionT]] = plugin_type


class NewPlugin[DefinitionT: ClassedPluginDefinition, PluginT](
    PluginManufacturer[DefinitionT, PluginT]
):
    """
    Configure a single plugin instance.
    """

    @final
    @override
    def __hash__(self):
        return hash((type(self), self.definition.plugin_type, self.id))

    @final
    @override
    async def _new(self, services: ServiceLevel, plugin: DefinitionT, /) -> PluginT:
        return await new(plugin.cls)


@final
class NewPluginDefinition[DefinitionT: ClassedPluginDefinition, PluginT](
    PluginManufacturerDefinition[DefinitionT, PluginT]
):
    """
    Define a plugin manufacturer.
    """

    def __init__(self, plugin_type: type[DefinitionT], /):
        super().__init__(plugin_type)
