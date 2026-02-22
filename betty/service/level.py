"""
Service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from betty.plugin.manager.service import ServiceLevelPluginManager

if TYPE_CHECKING:
    from betty.plugin.manager import PluginManager
    from betty.service.factory import Factory


class ServiceLevel:
    """
    A service level.
    """

    def __init__(self, *args: Any, plugins: PluginManager | None = None, **kwargs: Any):
        from betty.service.factory import Factory

        super().__init__(*args, **kwargs)
        self._factory = Factory(self)
        self._plugins = ServiceLevelPluginManager(self) if plugins is None else plugins

    @property
    def factory(self) -> Factory:
        """
        The object factory.
        """
        return self._factory

    @property
    def plugins(self) -> PluginManager:
        """
        The plugin manager.
        """
        return self._plugins


UNIVERSE: Final[ServiceLevel] = ServiceLevel()
"""
The universal service level.
"""
