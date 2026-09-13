"""
The classed plugin factory API.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Final, Self, final, override

from typing_extensions import disjoint_base

from betty.assertions.str import assert_str
from betty.attrs.machine_name import new_machine_name_attr
from betty.classtools import TypeABCMeta
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.factory import Manufacturable
from betty.freezer import Frozen
from betty.localizables.gettext import _
from betty.plugin.cls import ClassedPluginDefinition
from betty.plugin.resolve import (
    ResolvablePluginId,
    resolve_plugin_id,
)
from betty.porters.callback import CallbackPorter
from betty.prop import HasProps
from betty.service_level.factory import (
    Integratable,
    IntegratableFactory,
)
from betty.service_level.factory import (
    new as service_level_new,
)

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.service_level import ServiceLevel


type ManufacturablePlugin[PluginT] = (
    Intersection[PluginT, Manufacturable] | Intersection[PluginT, Callable[[], PluginT]]
)


type IntegratablePlugin[PluginT] = (
    Intersection[PluginT, Integratable] | ManufacturablePlugin[PluginT]
)


type PluginFactory[PluginT, NewPluginT: _NewPlugin] = (
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
class _NewPlugin[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    Data["NewPluginDefinition[PluginDefinitionT, PluginT]"],
    HasProps,
    Frozen,
    metaclass=TypeABCMeta,
):
    id = new_machine_name_attr(label=_("ID"))
    """
    The plugin ID.
    """

    def __init__(self, plugin_id: ResolvablePluginId[PluginDefinitionT], /):
        super().__init__()
        self.id = resolve_plugin_id(plugin_id)

    @abstractmethod
    def __hash__(self):
        pass

    @final
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return hash(self) == hash(other)

    @abstractmethod
    async def new(self, services: ServiceLevel, /) -> PluginT:
        """
        Create a new instance of the configured plugin.
        """

    @final
    @classmethod
    def resolve(cls, factory: PluginFactory[PluginT, Self]) -> Self:
        """
        Resolve a value to an instance of ``self``.
        """
        if isinstance(factory, cls):
            return factory
        return cls(resolve_plugin_id(factory))


class NewPlugin[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    _NewPlugin[PluginDefinitionT, PluginT]
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
class NewPluginDefinition[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    ObjectDefinition[NewPlugin[PluginDefinitionT, PluginT]]
):
    """
    Define a plugin factory.
    """

    def __init__(
        self,
        plugin_type: type[
            Intersection[PluginDefinitionT, ClassedPluginDefinition[PluginT]]
        ],
        /,
    ):
        super().__init__(
            label=plugin_type.type().label,
            porter=lambda definition: CallbackPorter(
                assert_str() | definition.cls, lambda data: data.id
            ),
        )
        self.plugin_type: Final[type[PluginDefinitionT]] = plugin_type
