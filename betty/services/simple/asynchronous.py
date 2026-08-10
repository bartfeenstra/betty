"""
Asynchronous simple services.
"""

from __future__ import annotations

from typing import final, override

from betty.asyncio import (
    LazyReAwaitable,
    ReAwaitable,
    ResolvableAwaitable,
    resolve_await,
)
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service import (
    HasServices,
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
)
from betty.typing import Intersection

type AsynchronousServiceFactory[OwnerT: HasServices, ServiceT] = ServiceFactory[
    OwnerT, ResolvableAwaitable[ServiceT]
]
type AsynchronousServiceOrFactory[OwnerT: HasServices, ServiceT] = ServiceOrFactory[
    OwnerT, ServiceT, ResolvableAwaitable[ServiceT]
]
type TypedAsynchronousServiceOrFactory[OwnerT: HasServices, ServiceT] = (
    ServiceT | AsynchronousServiceOrFactory[OwnerT, ServiceT]
)


@final
class AsynchronousServiceManager[
    OwnerT: Intersection[HasServices, ManagedLifeCycle],
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
