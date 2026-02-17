"""
Object factories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, final, overload

from betty.asyncio import resolve_await
from betty.data import Data
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.portable import PortableData
    from betty.service.level import ServiceLevel


class Manufacturable(ABC):
    """
    Allow this type to be instantiated using a :py:class:`betty.service.level.ServiceLevel`.
    """

    @classmethod
    @abstractmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        """
        Create a new instance using the given service level.
        """


class DataManufacturable[DataT: Data](ABC):
    """
    A class that can be initialized using defined data.
    """

    @classmethod
    @abstractmethod
    async def new(cls, services: ServiceLevel, data: DataT, /) -> Self:
        """
        Create a new instance using the given service level and defined data.
        """

    @classmethod
    @abstractmethod
    def new_data_cls(cls) -> type[DataT]:
        """
        The object's defined data class.
        """


@final
class Factory:
    """
    The object factory.
    """

    def __init__(self, services: ServiceLevel, /):
        self._services = services

    @overload
    async def new[ManufacturableT](
        self,
        target: type[ManufacturableT],
        data: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> ManufacturableT:
        pass

    @overload
    async def new[T](
        self,
        target: Callable[[], Awaitable[T] | T],
        data: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> T:
        pass

    @overload
    async def new[T](
        self,
        target: type[T],
        data: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> T:
        pass

    async def new(
        self,
        target,
        data=Void(),  # noqa: B008
    ):
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        if data is Void():
            if isinstance(target, type) and issubclass(target, Manufacturable):
                return await target.new(self._services)
            if callable(target):
                return await resolve_await(target())
            raise RuntimeError(f"Cannot create a new instance of {target}")
        if not isinstance(target, type) or not issubclass(target, DataManufacturable):
            raise HumanFacingException(
                _(
                    '"{target}" is not configurable, but configuration was given.'
                ).format(target=fully_qualified_name(target))
            )
        if not isinstance(data, Data):
            data = target.new_data_cls().data().porter.load(data)
        return await target.new(self._services, data)
