"""
Service levels.
"""

from __future__ import annotations

from collections import defaultdict
from importlib import metadata
from typing import TYPE_CHECKING, Any, Final

from betty.collection.keyed.adapter import KeyedCollectionAdapter
from betty.collection.keyed.error import ErroringKeyedCollection
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.error import PluginTypeNotFound
from betty.service.provider import service

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.collection.keyed import KeyedCollection
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.service.factory import Factory
    from betty.service.plugin import PluginManager


class _PluginTypeNotFound(PluginTypeNotFound, KeyError):
    pass


class ServiceLevel:
    """
    A service level.
    """

    def __init__(
        self,
        *args: Any,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._plugin_discovery = defaultdict(
            lambda: None, {} if plugins is None else plugins
        )

    @service
    def factory(self) -> Factory:
        """
        The object factory.
        """
        from betty.service.factory import Factory

        return Factory(self)

    @service
    def plugins(
        self,
    ) -> KeyedCollection[
        type[PluginDefinition],
        type[PluginDefinition] | MachineName | str,
        PluginManager,
    ]:
        """
        The available plugin types and plugins.
        """
        from betty.service.plugin import PluginManager

        def _resolve_plugin_type_id(
            key: type[PluginDefinition] | MachineName | str,
        ) -> MachineName:
            return (
                key.id
                if isinstance(key, PluginDefinition)
                else key.type().id
                if isinstance(key, type) and issubclass(key, PluginDefinition)
                else MachineName.resolve(key)
            )

        plugin_types = [
            entry_point.load()
            for entry_point in metadata.entry_points(group="betty.plugin")
        ]
        plugin_types.extend(self._plugin_discovery.keys())
        return ErroringKeyedCollection(
            KeyedCollectionAdapter(
                {
                    plugin_type.type().id: PluginManager(
                        self, plugin_type, self._plugin_discovery[plugin_type]
                    )
                    for plugin_type in plugin_types
                },  # ty:ignore[invalid-argument-type]
                key_resolver=_resolve_plugin_type_id,
            ),
            lambda error, key: _PluginTypeNotFound(
                _resolve_plugin_type_id(key), [x.type.type().id for x in self.plugins]
            ),
        )


UNIVERSE: Final[ServiceLevel] = ServiceLevel()
"""
The universal service level.
"""
