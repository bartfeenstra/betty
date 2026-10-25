"""
Service levels.
"""

from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING, Any, Final, override

from typing_extensions import disjoint_base

from betty.collections.catalog.dict import FrozenDictCatalog
from betty.definition.id import resolve_id
from betty.functools import raise_
from betty.life_cycle.manage import ManagedLifeCycle
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscoverer
from betty.prop import HasProps
from betty.services.simple import service
from betty.typing import empty_frozen_dict

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.factory import Factory
    from betty.plugin.discovery import ResolvableDiscovery

# @todo What is this for?
if TYPE_CHECKING:
    type Plugins = Mapping[
        type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
    ]
else:
    type Plugins = Any


class _Plugins(
    FrozenDictCatalog[
        MachineName, type[PluginDefinition] | MachineName | str, PluginDiscoverer
    ]
):
    @override
    def __getitem__[DefinitionT: PluginDefinition = PluginDefinition](
        self, key: type[DefinitionT] | MachineName | str
    ) -> PluginDiscoverer[DefinitionT]:
        return super().__getitem__(key)  # ty:ignore[invalid-return-type]


@disjoint_base
class ServiceLevel(HasProps, ManagedLifeCycle):
    """
    A service level.
    """

    def __init__(self, *args: Any, plugins: Plugins = empty_frozen_dict, **kwargs: Any):
        from betty.factory import Factory

        super().__init__(*args, **kwargs)
        self.factory: Final[Factory] = Factory(self)
        """
        The object factory.
        """
        self._plugin_discovery = plugins

    @service
    def plugins(
        self,
    ) -> _Plugins:
        """
        The available plugin types and plugins.
        """
        from betty.plugin.discovery import PluginDiscoverer
        from betty.plugin.error import PluginTypeNotFound

        class _PluginTypeNotFound(PluginTypeNotFound, KeyError):
            pass

        plugin_types = [
            entry_point.load()
            for entry_point in metadata.entry_points(group="betty.plugin")
        ]
        plugin_types.extend(self._plugin_discovery.keys())
        return _Plugins(
            {
                plugin_type.definition.id: PluginDiscoverer(
                    self,
                    plugin_type,
                    self._plugin_discovery.get(plugin_type, None),
                )
                for plugin_type in plugin_types
            },
            key=resolve_id,
            missing=lambda key: raise_(
                _PluginTypeNotFound(
                    resolve_id(key),
                    [x.type.definition.id for x in self.plugins],
                )
            ),
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
        super().__init__(*args, **kwargs)
        self.services: Final[ServiceLevelT] = services


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
