"""
Service containers.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from functools import update_wrapper
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, Protocol, Self, cast, overload, override

from betty.concurrent import AsynchronizedLock, Lock
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service import ServiceError
from betty.typing import Void

if TYPE_CHECKING:
    from types import FunctionType

    from ty_extensions import Intersection


type ServiceFactory[ManagedLifeCycleT: ManagedLifeCycle, ServiceT] = Callable[
    [ManagedLifeCycleT], ServiceT
]


class _ServiceDecorator[ManagedLifeCycleT: ManagedLifeCycle, ServiceT](Protocol):
    @overload
    def __call__(
        self, factory: Callable[[ManagedLifeCycleT], ServiceT], /
    ) -> _SynchronousServiceManager[ManagedLifeCycleT, ServiceT]:
        pass

    @overload
    def __call__(
        self, factory: Callable[[ManagedLifeCycleT], Awaitable[ServiceT]], /
    ) -> _AsynchronousServiceManager[ManagedLifeCycleT, ServiceT]:
        pass


@overload
def service[ManagedLifeCycleT: ManagedLifeCycle, ServiceT](
    factory: Callable[[ManagedLifeCycleT], Awaitable[ServiceT]], /
) -> _AsynchronousServiceManager[ManagedLifeCycleT, ServiceT]:
    pass


@overload
def service[ManagedLifeCycleT: ManagedLifeCycle, ServiceT](
    factory: Callable[[ManagedLifeCycleT], ServiceT], /
) -> _SynchronousServiceManager[ManagedLifeCycleT, ServiceT]:
    pass


@overload
def service(factory: None = None, /) -> _ServiceDecorator:
    pass


def service(factory):
    """
    Decorate a service factory method.

    The factory method is replaced with a :py:class:`service manager <betty.service.container.ServiceManager>` which
    handles lazy service instantiation, caching, and multiprocessing support.

    The decorated factory method should return a new service instance.
    """

    def _service[ManagedLifeCycleT: ManagedLifeCycle, ServiceT](
        factory: Callable[[ManagedLifeCycleT], ServiceT], /
    ) -> ServiceManager[ManagedLifeCycleT, ServiceT, Any]:
        if iscoroutinefunction(factory):
            return _AsynchronousServiceManager(
                factory,  # ty:ignore[invalid-argument-type]
            )  # ty:ignore[invalid-return-type]
        return _SynchronousServiceManager(
            factory,  # ty:ignore[invalid-argument-type]
        )

    if factory is None:
        return _service
    return _service(factory)


class ServiceManager[ManagedLifeCycleT: ManagedLifeCycle, ServiceGetT, ServiceT]:
    """
    Manages a single service for a service container.
    """

    def __init__(
        self,
        factory: Intersection[
            ServiceFactory[ManagedLifeCycleT, ServiceGetT], FunctionType
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
    def __get__(self, instance: None, owner: type[ManagedLifeCycleT]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: ManagedLifeCycleT, owner: type[ManagedLifeCycleT]
    ) -> ServiceGetT:
        pass

    def __get__(
        self, instance: ManagedLifeCycleT | None, owner: type[ManagedLifeCycleT]
    ) -> ServiceGetT | Self:
        if instance is None:
            return self

        return self.get(instance)

    def get(self, instance: ManagedLifeCycleT, /) -> ServiceGetT:
        """
        Get the service from an instance.
        """
        instance.assert_alive()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: ManagedLifeCycleT, /) -> ServiceGetT:
        pass

    def _get_attr(self, instance: ManagedLifeCycleT, /) -> ServiceT | Void:
        return getattr(instance, self._service_attr_name, Void())

    def _get_factory(
        self, instance: ManagedLifeCycleT, /
    ) -> ServiceFactory[ManagedLifeCycleT, ServiceGetT]:
        factory = cast(
            "ServiceFactory[ManagedLifeCycleT, ServiceGetT] | None",
            getattr(instance, self._factory_override_attr_name, None),
        )
        if factory is not None:
            return factory
        return self._factory

    def _assert_not_initialized(self, instance: ManagedLifeCycleT, /):
        if not isinstance(self._get_attr(instance), Void):
            raise ServiceInitializedError(
                f"{instance}.{self._service_name} was initialized already."
            )

    def override(self, instance: ManagedLifeCycleT, service: ServiceT, /) -> None:
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
        instance: ManagedLifeCycleT,
        factory: ServiceFactory[ManagedLifeCycleT, ServiceGetT],
        /,
    ) -> None:
        """
        Override the default service factory for the given instance.

        This MUST only be called from ``instance.__init__()``. It will override the existing service factory method
        defined on the instance.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._factory_override_attr_name, factory)


class _AsynchronousServiceManager[ManagedLifeCycleT: ManagedLifeCycle, ServiceT](
    ServiceManager[ManagedLifeCycleT, Awaitable[ServiceT], ServiceT],
):
    def _lock(self, instance: ManagedLifeCycleT, /) -> Lock:
        lock_attr_name = f"_{self._service_attr_name}_lock"
        try:
            return cast(Lock, getattr(instance, lock_attr_name))
        except AttributeError:
            lock = AsynchronizedLock.new_threadsafe()
            setattr(instance, lock_attr_name, lock)
            return lock

    @override
    async def _get(self, instance: ManagedLifeCycleT, /) -> ServiceT:
        async with self._lock(instance):
            service = self._get_attr(instance)

            if not isinstance(service, Void):
                return service

            new_service = await self._get_factory(instance)(instance)
            setattr(instance, self._service_attr_name, new_service)
            return new_service


class _SynchronousServiceManager[ManagedLifeCycleT: ManagedLifeCycle, ServiceT](
    ServiceManager[ManagedLifeCycleT, ServiceT, ServiceT]
):
    @override
    def _get(self, instance: ManagedLifeCycleT, /) -> ServiceT:
        service = self._get_attr(instance)
        if not isinstance(service, Void):
            return service

        new_service = self._get_factory(instance)(instance)
        setattr(instance, self._service_attr_name, new_service)
        return new_service


class ServiceInitializedError(ServiceError):
    """
    A service was unexpectedly initialized already.
    """
