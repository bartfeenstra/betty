"""
Service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from betty.life_cycle.manage import ManagedLifeCycle
from betty.plugin.manager.service import ServiceLevelPluginManager
from betty.service.factory import Factory

if TYPE_CHECKING:
    from betty.plugin.manager import PluginManager


class ServiceLevel(ManagedLifeCycle):
    """
    A service level.

    A runtime Betty environment consists of different service levels, as well as one or more types of service containers
    (that can provide services across the environment) within those levels.

    .. list-table:: Service levels and containers
       :widths: 25 25
       :header-rows: 1

       * - Level
         - Container(s)
       * - :py:data:`betty.service.level.UNIVERSE`
         - *N/A*
       * - :py:class:`betty.app.App`
         - :py:class:`betty.app.App`
       * - :py:class:`betty.project.Project`
         - :py:class:`betty.project.Project`
       * - :py:class:`betty.project.Project`
         - :py:class:`betty.extension.Extension`
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
    def plugins(self) -> PluginManager:
        """
        The plugin manager.
        """
        return self._plugins


UNIVERSE: Final[ServiceLevel] = ServiceLevel()
"""
The universal service level.
"""
