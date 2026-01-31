"""
The hydration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


_T = TypeVar("_T")


class Hydratable(ABC):
    """
    An object that can be hydrated from a service level.
    """

    @abstractmethod
    async def hydrate(self, *, services: ServiceLevel) -> None:
        """
        Hydrate ``self``.

        Hydration allows data definitions to require a :py:type:`betty.service.level.ServiceLevel` to perform tasks
        such as validation or enhancing the data using information or functionality from the service level.
        """


class Hydrator(Generic[_T]):
    """
    An object capable of hydrating other data.
    """

    async def hydrate(self, *, services: ServiceLevel, data: _T) -> None:
        """
        Hydrate data.

        Hydration allows data definitions to require a :py:type:`betty.service.level.ServiceLevel` to perform tasks
        such as validation or enhancing the data using information or functionality from the service level.
        """
