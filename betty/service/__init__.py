"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final, override

from betty.descriptor import Descriptor as Descriptor
from betty.descriptor import GettableDescriptor, HasDescriptors

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


class ServiceProvider(HasDescriptors):
    """
    A service provider.
    """

    def __init__(self, *args: Any, services: ServiceLevel, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__services = services

    @final
    @property
    def services(self) -> ServiceLevel:
        """
        The service level the services are provided for.
        """
        return self.__services


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
](GettableDescriptor[ServiceProviderT, GetServiceT]):
    """
    Manage a single service for a service provider.
    """

    def __init__(
        self, factory: ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT], /
    ):
        self.__service_or_factory = factory

    @final
    @property
    def id(self) -> str:
        """
        The global service ID.
        """
        return f"{self.descriptor_owner.__name__}.{self.descriptor_name}"

    @override
    def init_descriptor(self, instance: ServiceProviderT, /) -> None:
        self._assert_service_not_initialized(instance)
        setattr(
            instance,
            f"_service_{self.descriptor_name}",
            self._new_service_getter(instance),
        )

    @abstractmethod
    def _new_service_getter(self, instance: ServiceProviderT, /) -> GetterServiceT:
        """
        Create a new service getter.

        The getter is capable of lazily returning the service, creating a new one, returning a cache one, or returning
        a service override.

        The getter MUST be thread-safe.
        """

    @final
    @override
    def get(self, instance: ServiceProviderT, /) -> GetServiceT:
        return self._get_service(getattr(instance, f"_service_{self.descriptor_name}"))

    @abstractmethod
    def _get_service(self, service: GetterServiceT, /) -> GetServiceT:
        """
        Get the service from the getter.
        """

    @final
    def _get_service_or_factory(
        self, instance: ServiceProviderT, /
    ) -> ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT]:
        return getattr(
            instance,
            f"_service_{self.descriptor_name}_or_factory",
            self.__service_or_factory,
        )

    @final
    def _assert_service_not_initialized(self, instance: ServiceProviderT, /) -> None:
        if hasattr(instance, f"_service_{self.descriptor_name}"):
            raise ServiceAlreadyInitialized(
                f"{instance}.{self.descriptor_name} was initialized already."
            )

    @final
    def override(
        self,
        instance: ServiceProviderT,
        service: ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT],
        /,
    ) -> None:
        """
        Override the service for the given instance.

        Calling this will prevent the existing factory from being called.

        This MUST only be called from ``instance.__init__()``.
        """
        self._assert_service_not_initialized(instance)
        setattr(instance, f"_service_{self.descriptor_name}_or_factory", service)


class ServiceNotYetInitialized(ServiceError):
    """
    A service was unexpectedly not yet initialized.
    """


class ServiceAlreadyInitialized(ServiceError):
    """
    A service was unexpectedly initialized already.
    """
