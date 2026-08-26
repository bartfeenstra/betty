"""
Asynchronous services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import LazyReAwaitable, ReAwaitable
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.service import (
    ResolvableServiceLevelHasServices,
    ServiceManager,
    ServiceManufacturer,
    new,
)

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


class AsynchronousServiceManager[
    OwnerT: ResolvableServiceLevelHasServices,
    ServiceT,
    ServiceLevelT: ServiceLevel = ServiceLevel,
](
    ServiceManager[
        OwnerT, ServiceT, ReAwaitable[ServiceT], ReAwaitable[ServiceT], ServiceLevelT
    ],
):
    """
    Manage an asynchronous service.
    """

    @final
    @override
    def _init_manufacturer(
        self,
        owner: OwnerT,
        manufacturer: ServiceManufacturer[ServiceT, ServiceLevelT, OwnerT],
        /,
    ) -> ReAwaitable[ServiceT]:
        async def _asynchronous_service_resolver() -> ServiceT:
            service = await new(
                manufacturer,  # ty:ignore[invalid-argument-type]
                owner,
            )
            if isinstance(service, Bootstrappable | Shutdownable):
                await owner.life_cycle.synchronize(service)
            return service

        return LazyReAwaitable(_asynchronous_service_resolver)

    @final
    @override
    def _resolve(self, resolver: ReAwaitable[ServiceT], /) -> ReAwaitable[ServiceT]:
        return resolver
