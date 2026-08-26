"""
Synchronous services.
"""

from __future__ import annotations

from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, final, override

from betty.functools import LazyReCallable
from betty.nothing import Nothing, NothingType
from betty.service import (
    ResolvableServiceLevelHasServices,
    ServiceManager,
    ServiceManufacturer,
    new,
)

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel

type _Resolver[ServiceT] = Callable[[], ServiceT]


class SynchronousServiceManager[
    OwnerT: ResolvableServiceLevelHasServices,
    ServiceT,
    ServiceLevelT: ServiceLevel = ServiceLevel,
](ServiceManager[OwnerT, ServiceT, ServiceT, _Resolver[ServiceT], ServiceLevelT]):
    """
    Manage a synchronous service.
    """

    @override
    def post_init_owner(self, owner: OwnerT, /) -> None:
        super().post_init_owner(owner)

    @final
    @override
    def _init_manufacturer(
        self,
        owner: OwnerT,
        manufacturer: ServiceManufacturer[ServiceT, ServiceLevelT, OwnerT],
        /,
    ) -> _Resolver[ServiceT] | NothingType:
        if iscoroutinefunction(manufacturer):

            async def _init_coroutine_manufacturer() -> None:
                self.ownership.storage.set(owner, await new(manufacturer, owner))

            owner.life_cycle.on_bootstrap(_init_coroutine_manufacturer)
            return Nothing
        return LazyReCallable(
            lambda: new(
                manufacturer,  # ty:ignore[invalid-argument-type]
                owner,
            )
        )  # ty:ignore[invalid-return-type]

    @final
    @override
    def _resolve(self, resolver: _Resolver[ServiceT], /) -> ServiceT:
        return resolver()
