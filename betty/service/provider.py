"""
Service providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import update_wrapper
from inspect import getmembers, iscoroutinefunction
from typing import TYPE_CHECKING, Any, Self, final, overload, override

from betty.asyncio import (
    LazyReAwaitable,
    ReAwaitable,
    ResolvableAwaitable,
    resolve_await,
)
from betty.functools import LazyReCallable
from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service import ServiceError

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel
    from betty.typing import Intersection


class ServiceProvider:
    """
    A service provider.
    """

    def __init__(self, *args: Any, services: ServiceLevel, **kwargs: Any):
        super(*args, **kwargs)
        for _, member in getmembers(type(self)):
            if isinstance(member, ServiceManager):
                member.init(services, self)


@final
@dataclass(frozen=True)
class Service[ServiceT]:
    """
    Wrap a service so it can be type-checked as such.
    """

    service: ServiceT


type ServiceFactory[ServiceProviderT: ServiceProvider, FactoryServiceT] = Callable[
    [ServiceProviderT], FactoryServiceT
]
type ServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT, FactoryServiceT] = (
    Service[ServiceT] | ServiceFactory[ServiceProviderT, FactoryServiceT]
)


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

    def __set_name__(self, owner: type[ServiceProviderT], name: str) -> None:
        self.__service_name = name
        self.__service_getter_attr_name = f"_service_{name}"
        self.__service_or_factory_attr_name = f"_service_{name}_or_factory"

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

    @final
    def init(self, services: ServiceLevel, instance: ServiceProviderT, /) -> None:
        """
        Initialize the service.
        """
        self._assert_service_not_initialized(instance)
        setattr(
            instance,
            self.__service_getter_attr_name,
            self._new_service_getter(services, instance),
        )

    @abstractmethod
    def _new_service_getter(
        self, services: ServiceLevel, instance: ServiceProviderT, /
    ) -> GetterServiceT:
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
        return self._get_service(getattr(instance, self.__service_getter_attr_name))

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
            instance, self.__service_or_factory_attr_name, self.__service_or_factory
        )

    @final
    def _assert_service_not_initialized(self, instance: ServiceProviderT, /) -> None:
        if hasattr(instance, self.__service_getter_attr_name):
            raise ServiceInitializedError(
                f"{instance}.{self.__service_name} was initialized already."
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
        setattr(instance, self.__service_or_factory_attr_name, service)


type AsynchronousServiceFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceFactory[ServiceProviderT, ResolvableAwaitable[ServiceT]]
)
type AsynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceOrFactory[ServiceProviderT, ServiceT, ResolvableAwaitable[ServiceT]]
)
type TypedAsynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceT | AsynchronousServiceOrFactory[ServiceProviderT, ServiceT]
)


class AsynchronousServiceManager[
    ServiceProviderT: Intersection[ServiceProvider, ManagedLifeCycle],
    ServiceT,
](
    ServiceManager[
        ServiceProviderT,
        ServiceT,
        ReAwaitable[ServiceT],
        ReAwaitable[ServiceT],
        ResolvableAwaitable[ServiceT],
    ],
):
    """
    Manage an asynchronous service.
    """

    @final
    @override
    def _new_service_getter(
        self, services: ServiceLevel, instance: ServiceProviderT, /
    ) -> ReAwaitable[ServiceT]:
        async def _factory() -> ServiceT:
            factory = self._get_service_or_factory(instance)
            if isinstance(factory, Service):
                service = factory.service
            else:
                service = await resolve_await(factory(instance))
            if isinstance(service, LifeCycle):
                await instance.life_cycle.synchronize(service)
            return service

        return LazyReAwaitable(_factory)

    @override
    def _get_service(self, service: ReAwaitable[ServiceT], /) -> ReAwaitable[ServiceT]:
        return service


type SynchronousServiceFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceFactory[ServiceProviderT, ServiceT]
)
type SynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceOrFactory[ServiceProviderT, ServiceT, ServiceT]
)
type TypedSynchronousServiceOrFactory[ServiceProviderT: ServiceProvider, ServiceT] = (
    ServiceT | SynchronousServiceOrFactory[ServiceProviderT, ServiceT]
)


class SynchronousServiceManager[ServiceProviderT: ServiceProvider, ServiceT](
    ServiceManager[
        ServiceProviderT, ServiceT, ServiceT, Callable[[], ServiceT], ServiceT
    ]
):
    """
    Manage a synchronous service.
    """

    @final
    @override
    def _new_service_getter(
        self, services: ServiceLevel, instance: ServiceProviderT, /
    ) -> Callable[[], ServiceT]:
        def _factory() -> ServiceT:
            factory = self._get_service_or_factory(instance)
            if isinstance(factory, Service):
                return factory.service
            return factory(instance)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], ServiceT], /) -> ServiceT:
        return service()


class ServiceInitializedError(ServiceError):
    """
    A service was unexpectedly initialized already.
    """


@overload
def service[ServiceProviderT: ServiceProvider, ServiceT](
    factory: Callable[[ServiceProviderT], Awaitable[ServiceT]], /
) -> ServiceManager[
    ServiceProviderT,
    ServiceT,
    ReAwaitable[ServiceT],
    ReAwaitable[ServiceT],
    ResolvableAwaitable[ServiceT],
]:
    pass


@overload
def service[ServiceProviderT: ServiceProvider, ServiceT](
    factory: Callable[[ServiceProviderT], ServiceT], /
) -> ServiceManager[
    ServiceProviderT, ServiceT, ServiceT, Callable[[], ServiceT], ServiceT
]:
    pass


def service(factory):
    """
    Decorate a service factory method.

    The factory method is replaced with a :py:class:`service manager <betty.service.provider.ServiceManager>` which
    lazily initializes the service when it is accessed.

    The decorated factory method should return a new service instance.
    """
    service_manager_cls = (
        AsynchronousServiceManager
        if iscoroutinefunction(factory)
        else SynchronousServiceManager
    )
    return update_wrapper(
        service_manager_cls(factory),  # ty:ignore[invalid-argument-type]
        factory,
    )
