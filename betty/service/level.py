"""
Service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from betty.plugin.manager.service import ServiceLevelPluginManager
from betty.service.factory import Factory

if TYPE_CHECKING:
    from betty.plugin.manager import PluginManager


class ServiceLevel:
    """
    A service level.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._factory = Factory(self)
        self._plugins = ServiceLevelPluginManager(self)

    @property
    def factory(self) -> Factory:
        """
        The object factory.
        """
        return self._factory

    @property
    def plugin(self) -> PluginManager:
        """
        The plugin manager.
        """
        return self._plugins


UNIVERSE: Final[ServiceLevel] = ServiceLevel()
"""
The universal service level.
"""
