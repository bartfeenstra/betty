"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, final, override

from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps, Prop
from betty.typing import Intersection

if TYPE_CHECKING:
    from betty.service_level import ResolvableServiceLevel

type ServiceFactory[FactoryServiceT] = Callable[
    [ResolvableServiceLevelHasServices], FactoryServiceT
]
type ServiceOrFactory[ServiceT, FactoryServiceT] = (
    Service[ServiceT] | ServiceFactory[FactoryServiceT]
)


@final
@dataclass(frozen=True)
class Service[ServiceT]:
    """
    Wrap a service so it can be type-checked as such.
    """

    service: ServiceT


type ResolvableServiceLevelHasServices = Intersection[
    ResolvableServiceLevel, HasProps, ManagedLifeCycle
]


class ServiceManager[
    ServiceT,
    GetServiceT,
    GetterServiceT,
    FactoryServiceT,
](Prop[ResolvableServiceLevelHasServices, GetServiceT]):
    """
    Manage a single service for a service provider.
    """

    def __init__(self, factory: ServiceOrFactory[ServiceT, FactoryServiceT], /):
        self.__service_or_factory = factory

    @override
    def pre_init_owner(self, owner: ResolvableServiceLevelHasServices, /) -> None:
        owner.assert_not_initialized()
        setattr(
            owner,
            f"_service_{self.ownership.name}",
            self._new_service_getter(owner),
        )

    @abstractmethod
    def _new_service_getter(
        self, owner: ResolvableServiceLevelHasServices, /
    ) -> GetterServiceT:
        """
        Create a new service getter.

        The getter is capable of lazily returning the service, creating a new one, returning a cache one, or returning
        a service override.

        The getter MUST be thread-safe.
        """

    @final
    @override
    def get(self, owner: ResolvableServiceLevelHasServices, /) -> GetServiceT:
        return self._get_service(getattr(owner, f"_service_{self.ownership.name}"))

    @abstractmethod
    def _get_service(self, service: GetterServiceT, /) -> GetServiceT:
        """
        Get the service from the getter.
        """

    @final
    def _get_service_or_factory(
        self, owner: ResolvableServiceLevelHasServices, /
    ) -> ServiceOrFactory[ServiceT, FactoryServiceT]:
        return getattr(
            owner,
            f"_service_{self.ownership.name}_or_factory",
            self.__service_or_factory,
        )

    @final
    def override(
        self,
        owner: ResolvableServiceLevelHasServices,
        service: ServiceOrFactory[ServiceT, FactoryServiceT],
        /,
    ) -> None:
        """
        Override the service for the given service provider.

        Calling this will prevent the existing factory from being called.

        This MUST only be called from ``instance.__init__()``.
        """
        owner.assert_not_initialized()
        setattr(owner, f"_service_{self.ownership.name}_or_factory", service)
