"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, final, override

from betty.prop import HasProps, Prop

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


class ServiceError(RuntimeError):
    """
    A service API error.
    """


type ServiceFactory[ServiceProviderT: ServiceProvider, FactoryServiceT] = Callable[
    [ServiceProviderT], FactoryServiceT
]
type ServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT, FactoryServiceT] = (
    Service[ServiceT] | ServiceFactory[ServiceProviderT, FactoryServiceT]
)


class ServiceProvider(HasProps):
    """
    A service provider.
    """

    def __init__(self, *args: Any, services: ServiceLevel, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.services: Final[ServiceLevel] = services
        """
        The service level the services are provided for.
        """


@final
@dataclass(frozen=True)
class Service[ServiceT]:
    """
    Wrap a service so it can be type-checked as such.
    """

    service: ServiceT


class ServiceManager[
    ServiceProviderT: ServiceProvider,
    ServiceT,
    GetServiceT,
    GetterServiceT,
    FactoryServiceT,
](Prop[ServiceProviderT, GetServiceT]):
    """
    Manage a single service for a service provider.
    """

    def __init__(
        self, factory: ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT], /
    ):
        self.__service_or_factory = factory

    @override
    def init_owner(self, service_provider: ServiceProviderT, /) -> None:
        self._assert_service_not_initialized(service_provider)
        setattr(
            service_provider,
            f"_service_{self.prop.name}",
            self._new_service_getter(service_provider),
        )

    @abstractmethod
    def _new_service_getter(
        self, service_provider: ServiceProviderT, /
    ) -> GetterServiceT:
        """
        Create a new service getter.

        The getter is capable of lazily returning the service, creating a new one, returning a cache one, or returning
        a service override.

        The getter MUST be thread-safe.
        """

    @final
    @override
    def get(self, service_provider: ServiceProviderT, /) -> GetServiceT:
        return self._get_service(
            getattr(service_provider, f"_service_{self.prop.name}")
        )

    @abstractmethod
    def _get_service(self, service: GetterServiceT, /) -> GetServiceT:
        """
        Get the service from the getter.
        """

    @final
    def _get_service_or_factory(
        self, service_provider: ServiceProviderT, /
    ) -> ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT]:
        return getattr(
            service_provider,
            f"_service_{self.prop.name}_or_factory",
            self.__service_or_factory,
        )

    @final
    def _assert_service_not_initialized(
        self, service_provider: ServiceProviderT, /
    ) -> None:
        if hasattr(service_provider, f"_service_{self.prop.name}"):
            raise ServiceAlreadyInitialized(
                f"{service_provider}.{self.prop.name} was initialized already."
            )

    @final
    def override(
        self,
        service_provider: ServiceProviderT,
        service: ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT],
        /,
    ) -> None:
        """
        Override the service for the given service provider.

        Calling this will prevent the existing factory from being called.

        This MUST only be called from ``instance.__init__()``.
        """
        self._assert_service_not_initialized(service_provider)
        setattr(service_provider, f"_service_{self.prop.name}_or_factory", service)


class ServiceNotYetInitialized(ServiceError):
    """
    A service was unexpectedly not yet initialized.
    """


class ServiceAlreadyInitialized(ServiceError):
    """
    A service was unexpectedly initialized already.
    """
