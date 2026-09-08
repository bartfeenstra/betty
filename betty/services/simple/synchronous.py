"""
Synchronous simple services.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import final, override

from betty.functools import LazyReCallable
from betty.service import (
    ResolvableServiceLevelHasServices,
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
)

type SynchronousServiceFactory[ServiceT] = ServiceFactory[ServiceT]
type SynchronousServiceOrFactory[ServiceT] = ServiceOrFactory[ServiceT, ServiceT]
type TypedSynchronousServiceOrFactory[ServiceT] = (
    ServiceT | SynchronousServiceOrFactory[ServiceT]
)


@final
class SynchronousServiceManager[ServiceT](
    ServiceManager[ServiceT, ServiceT, Callable[[], ServiceT], ServiceT]
):
    """
    Manage a synchronous service.
    """

    @override
    def _new_service_getter(
        self, owner: ResolvableServiceLevelHasServices, /
    ) -> Callable[[], ServiceT]:
        def _factory() -> ServiceT:
            factory = self._get_service_or_factory(owner)
            if isinstance(factory, Service):
                return factory.service
            return factory(owner)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], ServiceT], /) -> ServiceT:
        return service()
