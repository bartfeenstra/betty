"""
Synchronous simple services.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import final, override

from betty.functools import LazyReCallable
from betty.prop import HasProps
from betty.service import (
    Service,
    ServiceFactory,
    ServiceManager,
    ServiceOrFactory,
)

type SynchronousServiceFactory[OwnerT: HasProps, ServiceT] = ServiceFactory[
    OwnerT, ServiceT
]
type SynchronousServiceOrFactory[OwnerT: HasProps, ServiceT] = ServiceOrFactory[
    OwnerT, ServiceT, ServiceT
]
type TypedSynchronousServiceOrFactory[OwnerT: HasProps, ServiceT] = (
    ServiceT | SynchronousServiceOrFactory[OwnerT, ServiceT]
)


@final
class SynchronousServiceManager[OwnerT: HasProps, ServiceT](
    ServiceManager[OwnerT, ServiceT, ServiceT, Callable[[], ServiceT], ServiceT]
):
    """
    Manage a synchronous service.
    """

    @override
    def _new_service_getter(self, owner: OwnerT, /) -> Callable[[], ServiceT]:
        def _factory() -> ServiceT:
            factory = self._get_service_or_factory(owner)
            if isinstance(factory, Service):
                return factory.service
            return factory(owner)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], ServiceT], /) -> ServiceT:
        return service()
