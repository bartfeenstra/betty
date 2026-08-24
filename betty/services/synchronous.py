"""
Synchronous services.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, final, override

from betty.functools import LazyReCallable
from betty.service import (
    ResolvableServiceLevelHasServices,
    ServiceManager,
    ServiceManufacturer,
    new,
)

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel

type _Resolver[ServiceT] = Callable[[], ServiceT]


class SynchronousServiceManager[OwnerT: ResolvableServiceLevelHasServices, ServiceT](
    ServiceManager[OwnerT, ServiceT, ServiceT, _Resolver[ServiceT]]
):
    """
    Manage a synchronous service.
    """

    @final
    @override
    def _new_resolver(
        self,
        owner: OwnerT,
        manufacturer: ServiceManufacturer[ServiceT, ServiceLevel, OwnerT],
        /,
    ) -> _Resolver[ServiceT]:
        return LazyReCallable(lambda: new(manufacturer, owner))

    @final
    @override
    def _resolve(self, resolver: _Resolver[ServiceT], /) -> ServiceT:
        return resolver()
