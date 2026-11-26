"""
Service levels.
"""

from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING, Any, Final, override

from typing_extensions import disjoint_base

from betty.classtools.init import Init
from betty.collections.catalog.dict import FrozenDictCatalog
from betty.collections.mapping.dict import empty_frozen_dict
from betty.definition.id import resolve_id
from betty.freezers.life_cycle import FrozenOnBootstrap
from betty.life_cycle.manage import ManagedLifeCycle
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.services.simple import service

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.definition.discover import Discovery
    from betty.factory import Factory
    from betty.plugin.repo import PluginRepository


type PluginDiscoveries = Mapping[type[PluginDefinition], Discovery[PluginDefinition]]


class _PluginRepositories(
    FrozenDictCatalog[
        MachineName, type[PluginDefinition] | MachineName | str, "PluginRepository"
    ]
):
    @override
    def __getitem__[DefinitionT: PluginDefinition = PluginDefinition](
        self, key: type[DefinitionT] | MachineName | str
    ) -> PluginRepository[DefinitionT]:
        return super().__getitem__(key)  # ty:ignore[invalid-return-type]


@disjoint_base
class ServiceLevel(FrozenOnBootstrap, Init, ManagedLifeCycle):
    """
    A service level.
    """

    def __init__(
        self,
        *args: Any,
        plugin_discoveries: PluginDiscoveries = empty_frozen_dict,
        **kwargs: Any,
    ):
        from betty.factory import Factory

        super().__init__(*args, **kwargs)
        self.factory: Final[Factory] = Factory(self)
        """
        The object factory.
        """
        self._plugin_discoveries = plugin_discoveries

    @service
    def plugins(self) -> _PluginRepositories:
        """
        The available plugin types and plugins.
        """
        from betty.plugin.repo import PluginRepository

        plugin_types = [
            entry_point.load()
            for entry_point in metadata.entry_points(group="betty.plugin")
        ]
        plugin_types.extend(self._plugin_discoveries)
        return _PluginRepositories(
            {
                plugin_type.definition.id: PluginRepository(
                    self,
                    plugin_type,
                    discovery=self._plugin_discoveries.get(plugin_type, None),
                )
                for plugin_type in plugin_types
            },
            key=resolve_id,
        )


class DownstreamServiceLevel[UpstreamT: ServiceLevel = ServiceLevel](ServiceLevel):
    """
    A service level that has another upstream service level.
    """

    def __init__(
        self,
        *args: Any,
        upstream: UpstreamT,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.upstream: Final[UpstreamT] = upstream
        """
        The upstream service level.
        """


@disjoint_base
class HasServiceLevel[ServiceLevelT: ServiceLevel = ServiceLevel]:
    """
    An object that exposes a service level.
    """

    def __init__(self, *args: Any, services: ServiceLevelT, **kwargs: Any):
        self.services: Final[ServiceLevelT] = services
        super().__init__(*args, **kwargs)


type ResolvableServiceLevel[ServiceLevelT: ServiceLevel = ServiceLevel] = (
    ServiceLevelT | HasServiceLevel[ServiceLevelT]
)


def resolve_service_level[ServiceLevelT: ServiceLevel = ServiceLevel](
    services: ResolvableServiceLevel[ServiceLevelT], /
) -> ServiceLevelT:
    """
    Resolve a value to a service level.
    """
    if isinstance(services, ServiceLevel):
        return services
    return services.services
