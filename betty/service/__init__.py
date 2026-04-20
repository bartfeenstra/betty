"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Self, final, overload

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


class ServiceProvider[ServiceLevelT: ServiceLevel]:
    """
    A service provider.
    """

    def __init__(self, *args: Any, services: ServiceLevelT, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__services = services
        for _, member in getmembers(type(self)):
            if isinstance(member, ServiceManager):
                member.init(self)

    @final
    @property
    def services(self) -> ServiceLevelT:
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
](ABC):
    """
    Manage a single service for a service provider.
    """

    def __init__(
        self, factory: ServiceOrFactory[ServiceProviderT, ServiceT, FactoryServiceT], /
    ):
        self.__service_or_factory = factory

    @final
    def __set_name__(self, owner: type[ServiceProviderT], name: str) -> None:
        self.__owner = owner
        self.__name = name

    @final
    @property
    def owner(self) -> type[ServiceProviderT]:
        """
        The class this service is located on.
        """
        return self.__owner

    @final
    @property
    def name(self) -> str:
        """
        The service name.
        """
        return self.__name

    @final
    @property
    def id(self) -> str:
        """
        The global service ID.
        """
        return f"{self.owner.__name__}.{self.name}"

    @overload
    def __get__(self, instance: None, owner: type[ServiceProviderT], /) -> Self:
        pass

    @overload
    def __get__(
        self, instance: ServiceProviderT, owner: type[ServiceProviderT] | None = None, /
    ) -> GetServiceT:
        pass

    @final
    def __get__(
        self,
        instance: ServiceProviderT | None,
        owner: type[ServiceProviderT] | None = None,
        /,
    ) -> GetServiceT | Self:
        if instance is None:
            return self

        return self.get(instance)

    def init(self, instance: ServiceProviderT, /) -> None:
        """
        Initialize the service.
        """
        self._assert_service_not_initialized(instance)
        setattr(instance, f"_service_{self.name}", self._new_service_getter(instance))

    @abstractmethod
    def _new_service_getter(self, instance: ServiceProviderT, /) -> GetterServiceT:
        """
        Create a new service getter.

        The getter is capable of lazily returning the service, creating a new one, returning a cache one, or returning
        a service override.

        The getter MUST be thread-safe.
        """

    @final
    def get(self, instance: ServiceProviderT, /) -> GetServiceT:
        """
        Get the service from an instance.
        """
        return self._get_service(getattr(instance, f"_service_{self.name}"))

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
            instance, f"_service_{self.name}_or_factory", self.__service_or_factory
        )

    @final
    def _assert_service_not_initialized(self, instance: ServiceProviderT, /) -> None:
        if hasattr(instance, f"_service_{self.name}"):
            raise ServiceAlreadyInitialized(
                f"{instance}.{self.name} was initialized already."
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
        setattr(instance, f"_service_{self.name}_or_factory", service)


class ServiceNotYetInitialized(ServiceError):
    """
    A service was unexpectedly not yet initialized.
    """


class ServiceAlreadyInitialized(ServiceError):
    """
    A service was unexpectedly initialized already.
    """
