"""
Asynchronous simple services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from ty_extensions import Intersection

from betty.asyncio import (
    LazyReAwaitable,
    ReAwaitable,
    ResolvableAwaitable,
    resolve_await,
)
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service import (
    ResolvableServiceLevelHasServices,
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
)

if TYPE_CHECKING:
    from betty.service_level import ResolvableServiceLevel

type AsynchronousServiceFactory[OwnerT: ResolvableServiceLevelHasServices, ServiceT] = (
    ServiceFactory[OwnerT, ResolvableAwaitable[ServiceT]]
)
type AsynchronousServiceOrFactory[
    OwnerT: ResolvableServiceLevelHasServices,
    ServiceT,
] = ServiceOrFactory[OwnerT, ServiceT, ResolvableAwaitable[ServiceT]]
type TypedAsynchronousServiceOrFactory[
    OwnerT: ResolvableServiceLevelHasServices,
    ServiceT,
] = ServiceT | AsynchronousServiceOrFactory[OwnerT, ServiceT]


@final
class AsynchronousServiceManager[
    OwnerT: Intersection[ResolvableServiceLevel, ManagedLifeCycle],
    ServiceT,
](
    ServiceManager[
        OwnerT,
        ServiceT,
        ReAwaitable[ServiceT],
        ReAwaitable[ServiceT],
        ResolvableAwaitable[ServiceT],
    ],
):
    """
    Manage an asynchronous service.
    """

    @override
    def _new_service_getter(self, owner: OwnerT, /) -> ReAwaitable[ServiceT]:
        async def _factory() -> ServiceT:
            factory = self._get_service_or_factory(owner)
            if isinstance(factory, Service):
                service = factory.service
            else:
                service = await resolve_await(factory(owner))
            if isinstance(service, Bootstrappable | Shutdownable):
                await owner.life_cycle.synchronize(service)
            return service

        return LazyReAwaitable(_factory)

    @override
    def _get_service(self, service: ReAwaitable[ServiceT], /) -> ReAwaitable[ServiceT]:
        return service
