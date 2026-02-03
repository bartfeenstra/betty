"""
Service levels.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Final, Generic, Self, overload

from typing_extensions import TypeVar

from betty.asyncio import resolve_await
from betty.data import Data
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.plugin.manager.service import ServiceLevelPluginManager
from betty.service.container import ServiceContainer
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.plugin.manager import PluginManager
    from betty.portable import PortableData

_T = TypeVar("_T")
_DataT = TypeVar("_DataT", bound=Data)


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

    @overload
    async def new_target(
        self,
        target: type[_ServiceLevelManufacturableT],
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> _ServiceLevelManufacturableT:
        pass

    @overload
    async def new_target(
        self,
        target: Callable[[], Awaitable[_T] | _T],
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> _T:
        pass

    @overload
    async def new_target(
        self,
        target: type[_T],
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> _T:
        pass

    async def new_target(
        self,
        target,
        configuration=Void(),  # noqa: B008
    ):
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        if configuration is Void():
            if isinstance(target, type) and issubclass(target, Manufacturable):
                return await target.new(services=self)
            if callable(target):
                return await resolve_await(target())
            raise RuntimeError(f"Cannot create a new instance of {target}")
        if not isinstance(target, type) or not issubclass(target, Configurable):
            raise HumanFacingException(
                _(
                    '"{target}" is not configurable, but configuration was given.'
                ).format(target=fully_qualified_name(target))
            )
        if not isinstance(configuration, Data):
            configuration = target.configuration_cls().data().porter.load(configuration)
        return await target.new(
            services=self,
            configuration=configuration,
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


class Manufacturable(ABC):
    """
    Allow this type to be instantiated using a :py:class:`betty.service.level.ServiceLevel`.
    """

    @classmethod
    @abstractmethod
    async def new(cls, *, services: ServiceLevel = universe) -> Self:
        """
        Create a new instance using the given service level.
        """


_ServiceLevelManufacturableT = TypeVar(
    "_ServiceLevelManufacturableT", bound=Manufacturable
)


class Configurable(ABC, Generic[_DataT]):
    """
    Any configurable object.
    """

    @classmethod
    @abstractmethod
    async def new(
        cls, *, services: ServiceLevel = universe, configuration: _DataT
    ) -> Self:
        """
        Create a new instance using the given service level and configuration.
        """

    @classmethod
    @abstractmethod
    def configuration_cls(cls) -> type[_DataT]:
        """
        The object's configuration class.
        """
