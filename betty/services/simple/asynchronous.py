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
from betty.importlib import fully_qualified_name
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps
from betty.service import (
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
)

type AsynchronousServiceFactory[OwnerT: HasProps, ServiceT] = ServiceFactory[
    OwnerT, ResolvableAwaitable[ServiceT]
]
type AsynchronousServiceOrFactory[OwnerT: HasProps, ServiceT] = ServiceOrFactory[
    OwnerT, ServiceT, ResolvableAwaitable[ServiceT]
]
type TypedAsynchronousServiceOrFactory[OwnerT: HasProps, ServiceT] = (
    ServiceT | AsynchronousServiceOrFactory[OwnerT, ServiceT]
)


@final
class AsynchronousServiceManager[OwnerT: HasProps, ServiceT](
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
                if isinstance(owner, ManagedLifeCycle):
                    await owner.life_cycle.synchronize(service)
                else:
                    raise TypeError(
                        f"Cannot synchronize {fully_qualified_name(type(service))}'s life cycle with {fully_qualified_name(type(owner))}, because the latter does not subclass {fully_qualified_name(ManagedLifeCycle)}."
                    )
            return service

        return LazyReAwaitable(_factory)

    @override
    def _get_service(self, service: ReAwaitable[ServiceT], /) -> ReAwaitable[ServiceT]:
        return service
