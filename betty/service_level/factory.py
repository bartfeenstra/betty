from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


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


# @todo Finish this
def new():
    raise NotImplementedError
