"""
Object factories.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Self, final, overload

from betty.asyncio import resolve_await
from betty.data import Data
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.service.level import ServiceLevel
from betty.typing import Void, VoidType

if TYPE_CHECKING:
    from betty.portable import PortableData


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


type Manufacturer[T] = (
    Callable[[ServiceLevel], Awaitable[T] | T] | Callable[[], Awaitable[T] | T]
)


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
        data: Data | PortableData | VoidType = Void,
        /,
    ) -> ManufacturableT:
        pass

    @overload
    async def new[T](
        self,
        target: Manufacturer[T],
        data: Data | PortableData | VoidType = Void,
        /,
    ) -> T:
        pass

    @overload
    async def new[T](
        self,
        target: type[T],
        data: Data | PortableData | VoidType = Void,
        /,
    ) -> T:
        pass

    async def new(
        self,
        target,
        data=Void,  # noqa: B008
    ):
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        if data is Void:
            if isinstance(target, type) and issubclass(target, Manufacturable):
                return await target.new(self._services)
            if callable(target):
                signature = inspect.signature(target)
                # If there is (at least) one positional argument, call the target with the service level.
                try:
                    signature.bind("")
                except TypeError:
                    result = target()
                else:
                    result = target(self._services)
                return await resolve_await(result)
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
