"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, final, override

from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps, Prop

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


type ServiceFactory[OwnerT: HasServices, FactoryServiceT] = Callable[
    [OwnerT], FactoryServiceT
]
type ServiceOrFactory[OwnerT: HasServices, ServiceT, FactoryServiceT] = (
    Service[ServiceT] | ServiceFactory[OwnerT, FactoryServiceT]
)


class HasServices[ServiceLevelT: ServiceLevel = ServiceLevel](
    ManagedLifeCycle, HasProps
):
    """
    An object that has services.
    """

    def __init__(self, *args: Any, services: ServiceLevelT, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.services: Final[ServiceLevelT] = services


@final
@dataclass(frozen=True)
class Service[ServiceT]:
    """
    Wrap a service so it can be type-checked as such.
    """

    service: ServiceT


class ServiceManager[
    OwnerT: HasServices,
    ServiceT,
    GetServiceT,
    GetterServiceT,
    FactoryServiceT,
](Prop[OwnerT, GetServiceT]):
    """
    Manage a single service for a service provider.
    """

    def __init__(self, factory: ServiceOrFactory[OwnerT, ServiceT, FactoryServiceT], /):
        self.__service_or_factory = factory

    @override
    def _pre_init_owner(self, owner: OwnerT, /) -> None:
        owner.assert_not_initialized()
        setattr(
            owner,
            f"_service_{self.prop.name}",
            self._new_service_getter(owner),
        )

    @abstractmethod
    def _new_service_getter(self, owner: OwnerT, /) -> GetterServiceT:
        """
        Create a new service getter.

        The getter is capable of lazily returning the service, creating a new one, returning a cache one, or returning
        a service override.

        The getter MUST be thread-safe.
        """

    @final
    @override
    def get(self, owner: OwnerT, /) -> GetServiceT:
        return self._get_service(getattr(owner, f"_service_{self.prop.name}"))

    @abstractmethod
    def _get_service(self, service: GetterServiceT, /) -> GetServiceT:
        """
        Get the service from the getter.
        """

    @final
    def _get_service_or_factory(
        self, owner: OwnerT, /
    ) -> ServiceOrFactory[OwnerT, ServiceT, FactoryServiceT]:
        return getattr(
            owner, f"_service_{self.prop.name}_or_factory", self.__service_or_factory
        )

    @final
    def override(
        self,
        owner: OwnerT,
        service: ServiceOrFactory[OwnerT, ServiceT, FactoryServiceT],
        /,
    ) -> None:
        """
        Override the service for the given service provider.

        Calling this will prevent the existing factory from being called.

        This MUST only be called from ``instance.__init__()``.
        """
        owner.assert_not_initialized()
        setattr(owner, f"_service_{self.prop.name}_or_factory", service)
