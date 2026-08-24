"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from inspect import signature
from typing import TYPE_CHECKING, Any, cast, final, overload, override

from betty.asyncio import resolve_await
from betty.factory import Manufacturer
from betty.life_cycle.manage import ManagedLifeCycle
from betty.nothing import Nothing, NothingType
from betty.objecttools import AttrOperators
from betty.prop import HasProps, Prop
from betty.service_level import ServiceLevel
from betty.typing import Intersection, Not

if TYPE_CHECKING:
    from betty.service_level import ResolvableServiceLevel


type ServiceType[_ServiceT] = Intersection[_ServiceT, Not[Service], Not[NothingType]]


type ResolvableServiceLevelHasServices = Intersection[
    ResolvableServiceLevel, HasProps, ManagedLifeCycle
]


type _ManufacturerReturn[ServiceT: ServiceType] = (
    ServiceT | Coroutine[Any, Any, ServiceT]
)


type _OwnerDependentServiceManufacturer[
    ServiceT: ServiceType,
    ServiceLevelT: ServiceLevel,
    OwnerT: ResolvableServiceLevelHasServices,
] = Callable[[ServiceLevelT, OwnerT], _ManufacturerReturn[ServiceT]]


type ServiceManufacturer[
    ServiceT: ServiceType,
    ServiceLevelT: ServiceLevel,
    OwnerT: ResolvableServiceLevelHasServices,
] = (
    Manufacturer[ServiceT, ServiceLevelT]
    | _OwnerDependentServiceManufacturer[ServiceT, ServiceLevelT, OwnerT]
)


async def new[OwnerT: ResolvableServiceLevelHasServices, ServiceT: ServiceType](
    manufacturer: ServiceManufacturer[ServiceT, ServiceLevel, OwnerT], owner: OwnerT, /
) -> ServiceT:
    """
    Create a new service from a manufacturer.
    """
    from betty.service_level import resolve_service_level

    services = resolve_service_level(owner)
    if (
        not isinstance(manufacturer, type)
        and len(signature(manufacturer).parameters) == 2
    ):
        return resolve_await(
            cast(_OwnerDependentServiceManufacturer, manufacturer)(services, owner)
        )
    return await services.factory.new(manufacturer)


@final
@dataclass(frozen=True)
class Service[ServiceT: ServiceType]:
    """
    Wrap a service so it can be type-checked as such.
    """

    service: ServiceT


@overload
def wrap[ServiceT: ServiceType](
    init: ServiceT, guard: type[ServiceT], /
) -> Service[ServiceT]:
    pass


@overload
def wrap[T: Not[ServiceType]](init: T, guard: type[ServiceType], /) -> T:
    pass


def wrap(init, guard, /):
    """
    Wrap a service in a :py:class:`betty.service.Service`.
    """
    if isinstance(init, guard):
        return Service(init)
    return init


type ServiceInit[
    ServiceT: ServiceType,
    ServiceLevelT: ServiceLevel,
    OwnerT: ResolvableServiceLevelHasServices,
] = Service[ServiceT] | ServiceManufacturer[OwnerT, ServiceT, ServiceLevelT]


type WrappableServiceInit[
    ServiceT: ServiceType,
    ServiceLevelT: ServiceLevel,
    OwnerT: ResolvableServiceLevelHasServices,
] = ServiceT | ServiceInit[OwnerT, ServiceT, ServiceLevelT]


type OptionalWrappableServiceInit[
    ServiceT: ServiceType,
    ServiceLevelT: ServiceLevel,
    OwnerT: ResolvableServiceLevelHasServices,
] = WrappableServiceInit[ServiceT | NothingType, ServiceLevelT, OwnerT] | NothingType


class ServiceManager[
    OwnerT: ResolvableServiceLevelHasServices,
    ServiceT: ServiceType,
    GetT,
    ResolverT,
](Prop[OwnerT, GetT, ServiceInit[ServiceT, ServiceLevel, OwnerT] | NothingType]):
    """
    Manage a single service for a service provider.
    """

    __service_init_storage: AttrOperators[OwnerT]

    def __init__(self, manufacturer: ServiceInit[ServiceT, ServiceLevel, OwnerT], /):
        self.__service_init = manufacturer

    @override
    def __set_name__(self, owner: type[OwnerT], name: str):
        super().__set_name__(owner, name)
        self.__service_init_storage = AttrOperators(
            f"{self.ownership.storage.name}_service_init"
        )

    @override
    def post_init_owner(self, owner: OwnerT, /) -> None:
        service_init = self.__service_init_storage.get(owner, Nothing)
        if service_init is Nothing:
            service_init = self.__service_init
        self.ownership.storage.set(
            owner,
            service_init
            if isinstance(service_init, Service)
            else self._new_resolver(owner, service_init),
        )

    @abstractmethod
    def _new_resolver(
        self,
        owner: OwnerT,
        manufacturer: ServiceManufacturer[ServiceT, ServiceLevel, OwnerT],
        /,
    ) -> ResolverT:
        """
        Create a new service resolver.

        The resolver is capable of lazily returning the service, creating a new one, returning a cached one, or
        returning a service override.

        The resolver MUST be thread-safe.
        """

    @final
    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self._resolve(self.ownership.storage.get(owner))

    @abstractmethod
    def _resolve(self, resolver: ResolverT, /) -> GetT:
        """
        Resolve the service.
        """

    @final
    @override
    def is_settable(self, owner: OwnerT, /) -> bool:
        return not owner.is_initialized

    @final
    @override
    def set(
        self,
        owner: OwnerT,
        service: ServiceInit[ServiceT, ServiceLevel, OwnerT] | NothingType,
        /,
    ) -> None:
        self.assert_settable(owner)
        self.__service_init_storage.set(owner, service)
