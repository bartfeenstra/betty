"""
Service levels.
"""

from __future__ import annotations

from collections import defaultdict
from importlib import metadata
from typing import TYPE_CHECKING, Any, Final

from betty.collections.keyed.adapter import KeyedCollectionAdapter
from betty.life_cycle.manage import ManagedLifeCycle
from betty.plugin.resolve import resolve_plugin_type_id
from betty.service import ServiceProvider
from betty.services.simple import service

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.collections.plugin.discoverer import PluginDiscovererCollection
    from betty.factory import Factory
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery

if TYPE_CHECKING:
    type Plugins = Mapping[
        type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
    ]
else:
    type Plugins = Any


class ServiceLevel(ManagedLifeCycle, ServiceProvider):
    """
    A service level.
    """

    def __init__(self, *args: Any, plugins: Plugins | None = None, **kwargs: Any):
        from betty.factory import Factory

        super().__init__(*args, services=self, **kwargs)
        self.factory: Final[Factory] = Factory(self)
        """
        The object factory.
        """
        self._plugin_discovery = defaultdict(
            lambda: None, {} if plugins is None else plugins
        )

    @service
    def plugins(self) -> PluginDiscovererCollection:
        """
        The available plugin types and plugins.
        """
        from betty.collections.plugin.discoverer import PluginDiscovererCollection
        from betty.plugin.discovery import PluginDiscoverer
        from betty.plugin.error import PluginTypeNotFound

        class _PluginTypeNotFound(PluginTypeNotFound, KeyError):
            pass

        plugin_types = [
            entry_point.load()
            for entry_point in metadata.entry_points(group="betty.plugin")
        ]
        plugin_types.extend(self._plugin_discovery.keys())
        return PluginDiscovererCollection(
            KeyedCollectionAdapter(
                {
                    plugin_type.type().id: PluginDiscoverer(
                        self, plugin_type, self._plugin_discovery[plugin_type]
                    )
                    for plugin_type in plugin_types
                },
                key_resolver=resolve_plugin_type_id,
            ),
            lambda error, key: _PluginTypeNotFound(
                resolve_plugin_type_id(key), [x.type.type().id for x in self.plugins]
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
