"""
Service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final

from typing_extensions import TypeVar, override

from betty.config import Configurable
from betty.data import Data
from betty.exception import HumanFacingException
from betty.factory import new_target
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.plugin.manager.service import ServiceLevelPluginManager
from betty.service.container import ServiceContainer
from betty.typing import Void

if TYPE_CHECKING:
    from betty.plugin.manager import PluginManager
    from betty.portable import PortableData
    from betty.service.level.factory import ServiceLevelTarget

_T = TypeVar("_T")


class ServiceLevel(ServiceContainer):
    """
    A service level.

    A runtime Betty environment consists of different service levels, as well as one or more types of service containers
    (that can provide services across the environment) within those levels.

    .. list-table:: Service levels and containers
       :widths: 25 25
       :header-rows: 1

       * - Level
         - Container(s)
       * - :py:data:`betty.service.level.universe`
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
        self._plugins = ServiceLevelPluginManager(self)

    @final
    async def new_target(
        self,
        target: ServiceLevelTarget[_T],
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        return await self._new_target(target, configuration)

    @final
    @override
    async def _new_target(
        self,
        target: ServiceLevelTarget[_T],
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> _T:
        from betty.service.level.factory import ServiceLevelDependentSelfFactory

        if configuration is Void():
            if isinstance(target, type) and issubclass(
                target, ServiceLevelDependentSelfFactory
            ):
                return await target.new_for_services(services=self)  # ty:ignore[invalid-return-type]
            return await new_target(target)
        if not isinstance(target, type) or not issubclass(target, Configurable):
            raise HumanFacingException(
                _(
                    '"{target}" is not configurable, but configuration was given.'
                ).format(target=fully_qualified_name(target))
            )
        if not isinstance(configuration, Data):
            configuration = target.configuration_cls().data().porter.load(configuration)  # ty:ignore[unresolved-attribute]
        return await target.new_for_configuration(
            services=self,
            configuration=configuration,  # ty:ignore[invalid-argument-type]
        )  # ty:ignore[invalid-return-type]

    @override
    async def _post_bootstrap(self) -> None:
        from betty.config import Configurable

        if isinstance(self, Configurable):
            configuration = self.configuration
            if isinstance(configuration, Data):
                await configuration.data().hydrate(
                    services=self,
                    data=configuration,  # ty:ignore[invalid-argument-type]
                )

    @property
    def plugins(self) -> PluginManager:
        """
        The plugin manager.
        """
        return self._plugins


universe: Final[ServiceLevel] = ServiceLevel()
"""
The universal service level.
"""
