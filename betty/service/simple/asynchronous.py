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
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
    ServiceProvider,
)
from betty.typing import Intersection

type AsynchronousServiceFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceFactory[ServiceProviderT, ResolvableAwaitable[ServiceT]]
)
type AsynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceOrFactory[ServiceProviderT, ServiceT, ResolvableAwaitable[ServiceT]]
)
type TypedAsynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceT | AsynchronousServiceOrFactory[ServiceProviderT, ServiceT]
)


@final
class AsynchronousServiceManager[
    ServiceProviderT: Intersection[ServiceProvider, ManagedLifeCycle],
    ServiceT,
](
    ServiceManager[
        ServiceProviderT,
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
        self, service_provider: ServiceProviderT, /
    ) -> ReAwaitable[ServiceT]:
        async def _factory() -> ServiceT:
            factory = self._get_service_or_factory(service_provider)
            if isinstance(factory, Service):
                service = factory.service
            else:
                service = await resolve_await(factory(service_provider))
            if isinstance(service, Bootstrappable | Shutdownable):
                await service_provider.life_cycle.synchronize(service)
            return service

        return LazyReAwaitable(_factory)

    @override
    def _get_service(self, service: ReAwaitable[ServiceT], /) -> ReAwaitable[ServiceT]:
        return service
