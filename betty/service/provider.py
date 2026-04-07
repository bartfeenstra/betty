"""
Service providers.
"""

from __future__ import annotations

import threading
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from functools import update_wrapper
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, Protocol, Self, cast, overload, override

from betty.concurrent import AsynchronizedLock, Ledger
from betty.life_cycle import LifeCycle
from betty.service import ServiceError
from betty.typing import Void, VoidType

if TYPE_CHECKING:
    from types import FunctionType

    from betty.typing import Intersection


class ServiceProvider:
    """
    A service provider.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()
        self._ledger = Ledger(AsynchronizedLock(self._lock))


type ServiceFactory[ServiceProviderT: ServiceProvider, ServiceT] = Callable[
    [ServiceProviderT], ServiceT
]


class _ServiceDecorator[ServiceProviderT: ServiceProvider, ServiceT](Protocol):
    @overload
    def __call__(
        self, factory: Callable[[ServiceProviderT], ServiceT], /
    ) -> _SynchronousServiceManager[ServiceProviderT, ServiceT]:
        pass

    @overload
    def __call__(
        self, factory: Callable[[ServiceProviderT], Awaitable[ServiceT]], /
    ) -> _AsynchronousServiceManager[ServiceProviderT, ServiceT]:
        pass


@overload
def service[ServiceProviderT: ServiceProvider, ServiceT](
    factory: Callable[[ServiceProviderT], Awaitable[ServiceT]], /
) -> _AsynchronousServiceManager[ServiceProviderT, ServiceT]:
    pass


@overload
def service[ServiceProviderT: ServiceProvider, ServiceT](
    factory: Callable[[ServiceProviderT], ServiceT], /
) -> _SynchronousServiceManager[ServiceProviderT, ServiceT]:
    pass


@overload
def service() -> _ServiceDecorator:
    pass


def service(factory=None):
    """
    Decorate a service factory method.

    The factory method is replaced with a :py:class:`service manager <betty.service.provider.ServiceManager>` which
    handles lazy service instantiation, caching, and multiprocessing support.

    The decorated factory method should return a new service instance.
    """

    def _service(factory):  # noqa: ANN001, ANN202
        if iscoroutinefunction(factory):
            return _AsynchronousServiceManager(factory)
        return _SynchronousServiceManager(factory)

    if factory is None:
        return _service
    return _service(factory)


class ServiceManager[ServiceProviderT: ServiceProvider, ServiceGetT, ServiceT]:
    """
    Manages a single service for a service provider.
    """

    def __init__(
        self,
        factory: Intersection[
            ServiceFactory[ServiceProviderT, ServiceGetT], FunctionType
        ],
        /,
    ):
        update_wrapper(
            self,  # ty:ignore[invalid-argument-type]
            factory,
        )
        self._factory = factory
        self._service_name: str = factory.__name__
        self._service_attr_name = f"_{self._service_name}"
        self._service_override_attr_name = f"{self._service_attr_name}_override"
        self._factory_override_attr_name = f"{self._service_attr_name}_factory_override"

    @property
    def name(self) -> str:
        """
        The service name.
        """
        return self._service_name

    @overload
    def __get__(self, instance: None, owner: type[ServiceProviderT], /) -> Self:
        pass

    @overload
    def __get__(
        self, instance: ServiceProviderT, owner: type[ServiceProviderT] | None = None, /
    ) -> ServiceGetT:
        pass

    def __get__(
        self,
        instance: ServiceProviderT | None,
        owner: type[ServiceProviderT] | None = None,
        /,
    ) -> ServiceGetT | Self:
        if instance is None:
            return self

        return self.get(instance)

    def get(self, instance: ServiceProviderT, /) -> ServiceGetT:
        """
        Get the service from an instance.
        """
        if isinstance(instance, LifeCycle):
            instance.assert_alive()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: ServiceProviderT, /) -> ServiceGetT:
        pass

    def _get_attr(self, instance: ServiceProviderT, /) -> ServiceT | VoidType:
        return getattr(instance, self._service_attr_name, Void)

    def _get_factory(
        self, instance: ServiceProviderT, /
    ) -> ServiceFactory[ServiceProviderT, ServiceGetT]:
        factory = cast(
            "ServiceFactory[ServiceProviderT, ServiceGetT] | None",
            getattr(instance, self._factory_override_attr_name, None),
        )
        if factory is not None:
            return factory
        return self._factory

    def _assert_not_initialized(self, instance: ServiceProviderT, /) -> None:
        if self._get_attr(instance) is not Void:
            raise ServiceInitializedError(
                f"{instance}.{self._service_name} was initialized already."
            )

    def override(self, instance: ServiceProviderT, service: ServiceT, /) -> None:
        """
        Override the service for the given instance.

        Calling this will prevent any existing factory from being called.

        This MUST only be called from ``instance.__init__()``.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._service_attr_name, service)
        setattr(instance, self._service_override_attr_name, True)

    def override_factory(
        self,
        instance: ServiceProviderT,
        factory: ServiceFactory[ServiceProviderT, ServiceGetT],
        /,
    ) -> None:
        """
        Override the default service factory for the given instance.

        This MUST only be called from ``instance.__init__()``. It will override the existing service factory method
        defined on the instance.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._factory_override_attr_name, factory)


class _AsynchronousServiceManager[ServiceProviderT: ServiceProvider, ServiceT](
    ServiceManager[ServiceProviderT, Awaitable[ServiceT], ServiceT],
):
    @override
    async def _get(self, instance: ServiceProviderT, /) -> ServiceT:
        async with instance._ledger.ledger(self.name):
            service = self._get_attr(instance)

            if service is not Void:
                return service

            new_service = await self._get_factory(instance)(instance)
            setattr(instance, self._service_attr_name, new_service)
            return new_service


class _SynchronousServiceManager[ServiceProviderT: ServiceProvider, ServiceT](
    ServiceManager[ServiceProviderT, ServiceT, ServiceT]
):
    @override
    def _get(self, instance: ServiceProviderT, /) -> ServiceT:
        with instance._lock:
            service = self._get_attr(instance)
            if service is not Void:
                return service

            new_service = self._get_factory(instance)(instance)
            setattr(instance, self._service_attr_name, new_service)
            return new_service


class ServiceInitializedError(ServiceError):
    """
    A service was unexpectedly initialized already.
    """
