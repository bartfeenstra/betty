"""
The hydration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


_T = TypeVar("_T")


class Hydratable(ABC):
    """
    An object that can be hydrated from a service level.
    """

    @abstractmethod
    async def hydrate(self, services: ServiceLevel, /) -> None:
        """
        Hydrate ``self``.

        Hydration allows data definitions to require a :py:type:`betty.service.level.ServiceLevel` to perform tasks
        such as validation or enhancing the data using information or functionality from the service level.
        """


# @todo The problem with taking this out of DataDefinition and using a visitor pattern is that it means
# @todo Hydratable.hydrate() is no longer supposed to be called directly. I mean, was it ever?
# @todo Or in other words: where does this API belong, what does it act on, and what should be the universal entry point?
# @todo - Currently, everything that is Hydratable is also defined data.
# @todo - If that stays, then hydration is a service/data intersection API, not just service API.
# @todo - Does it make sense for anything else to be hydratable? Not really, this whole thing is a roundabout way
# @todo   of letting value objects access services.
# @todo - What if some data is not Hydratable but we want to add some kind of hydration? E.g. a third party's class we
# @todo   want to validate through hydration?
# @todo
# @todo
async def hydrate(services: ServiceLevel, data: object, /) -> None:
    """
    Hydrate data.

    Hydration allows data definitions to require a :py:type:`betty.service.level.ServiceLevel` to perform tasks
    such as validation or enhancing the data using information or functionality from the service level.
    """
    if isinstance(data, Hydratable):
        await data.hydrate(services)
