"""
The service level factory API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Self

from betty.factory import Factory
from betty.factory import new as new_manufacturable

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.service_level import ServiceLevel


class Integrator[T](metaclass=ABCMeta):
    """
    A class that can initialize an object asynchronously for a service level.
    """

    @abstractmethod
    async def new(self, services: ServiceLevel, /) -> T:
        """
        Create a new instance.
        """


class Integratable(metaclass=ABCMeta):
    """
    A class that can be initialized asynchronously for a service level.
    """

    @classmethod
    @abstractmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        """
        Create a new instance.
        """


type IntegratableFactory[T] = (
    type[Intersection[T, Integratable] | Integrator[T]] | Factory[T]
)


async def new[T](cls: Factory[T], services: ServiceLevel, /) -> T:
    """
    Create a new instance of the given class for the given service level.
    """
    if isinstance(cls, (Integratable, Integrator)):
        return await cls.new(services)
    return await new_manufacturable(cls)
