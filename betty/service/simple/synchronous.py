"""
Synchronous simple services.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import final, override

from betty.functools import LazyReCallable
from betty.service import (
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
    ServiceProvider,
)

type SynchronousServiceFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceFactory[ServiceProviderT, ServiceT]
)
type SynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceOrFactory[ServiceProviderT, ServiceT, ServiceT]
)
type TypedSynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceT | SynchronousServiceOrFactory[ServiceProviderT, ServiceT]
)


@final
class SynchronousServiceManager[ServiceProviderT: ServiceProvider, ServiceT](
    ServiceManager[
        ServiceProviderT, ServiceT, ServiceT, Callable[[], ServiceT], ServiceT
    ]
):
    """
    Manage a synchronous service.
    """

    @override
    def _new_service_getter(
        self, instance: ServiceProviderT, /
    ) -> Callable[[], ServiceT]:
        def _factory() -> ServiceT:
            factory = self._get_service_or_factory(instance)
            if isinstance(factory, Service):
                return factory.service
            return factory(instance)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], ServiceT], /) -> ServiceT:
        return service()
