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
from betty.service import (
    ResolvableServiceLevelHasServices,
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
)

type AsynchronousServiceFactory[ServiceT] = ServiceFactory[
    ResolvableAwaitable[ServiceT]
]
type AsynchronousServiceOrFactory[ServiceT] = ServiceOrFactory[
    ServiceT, ResolvableAwaitable[ServiceT]
]
type TypedAsynchronousServiceOrFactory[ServiceT] = (
    ServiceT | AsynchronousServiceOrFactory[ServiceT]
)


@final
class AsynchronousServiceManager[ServiceT](
    ServiceManager[
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
    def _new_service_getter(
        self, owner: ResolvableServiceLevelHasServices, /
    ) -> ReAwaitable[ServiceT]:
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
