"""
Object factories.
"""

from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from collections.abc import Awaitable, Callable
from inspect import Parameter
from typing import Self, final, overload

from betty.asyncio import resolve_await
from betty.data import Data
from betty.importlib import fully_qualified_name
from betty.service_level import ServiceLevel


class FactoryError(RuntimeError):
    """
    Raised when a factory could not create an object.
    """


class UnsupportedTarget(FactoryError):
    """
    Raised when a factory target cannot be used to create a new object.
    """


class TargetError(FactoryError):
    """
    Raised when a target raised an error while creating a new object.
    """


class Manufacturable(metaclass=ABCMeta):
    """
    Allow this type to be instantiated using a :py:class:`betty.service_level.ServiceLevel`.
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


type FactoryTarget = type[Manufacturable] | Manufacturer


class DataManufacturable[DataT: Data](metaclass=ABCMeta):
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
    async def new[ManufacturableT: Manufacturable](
        self, target: type[ManufacturableT], /
    ) -> ManufacturableT:
        pass

    @overload
    async def new[T](self, target: Manufacturer[T], /) -> T:
        pass

    async def new(self, target, /):
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        if isinstance(target, type) and issubclass(target, Manufacturable):
            return await target.new(self._services)
        args = self._args(target)
        if args is None:
            raise UnsupportedTarget(
                f'{target} must not have any required arguments, except optionally a first argument typed on {fully_qualified_name(ServiceLevel)} and/or named "services".'
            )
        try:
            return await resolve_await(target(*args))
        except Exception as error:
            raise TargetError(
                f"{repr(target)} raised an unexpected error when creating a new object."
            ) from error

    def _args(self, target: FactoryTarget) -> tuple | None:
        parameters = tuple(inspect.signature(target).parameters.values())
        if not parameters:
            return ()
        if (
            parameters[0].annotation is ServiceLevel or parameters[0].name == "services"
        ) and self._optional(*parameters[1:]):
            return (self._services,)
        if self._optional(*parameters):
            return ()
        return None

    def _optional(self, *parameters: Parameter) -> bool:
        return all(
            parameter.default is not Parameter.empty
            or parameter.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD)
            for parameter in parameters
        )
