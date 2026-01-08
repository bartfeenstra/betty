"""
The hydration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


class Hydratable(ABC):
    """
    An object that can be hydrated from a service level.
    """

    @abstractmethod
    async def hydrate(self, services: ServiceLevel, /) -> None:
        """
        Hydrate the object.

        Hydration allows data definitions to require a :py:type:`betty.service.level.ServiceLevel` to perform tasks
        such as validation or enhancing the data using information or functionality from the service level.
        """
