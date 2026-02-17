"""
Service containers.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from functools import update_wrapper
from inspect import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    cast,
    overload,
    override,
)

from betty.concurrent import AsynchronizedLock, Lock
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service import ServiceError
from betty.typing import Void, internal

if TYPE_CHECKING:
    from types import FunctionType

    from ty_extensions import Intersection


_T = TypeVar("_T")
_ServiceT = TypeVar("_ServiceT")
_ServiceGetT = TypeVar("_ServiceGetT")
_ManagedLifeCycleT = TypeVar("_ManagedLifeCycleT", bound=ManagedLifeCycle)


ServiceFactory: TypeAlias = Callable[[_ManagedLifeCycleT], _ServiceT]


class _ServiceDecorator(Protocol):
    @overload
    def __call__(
        self, factory: Callable[[_ManagedLifeCycleT], _ServiceT], /
    ) -> _SynchronousServiceManager[_ManagedLifeCycleT, _ServiceT]:
        pass

    @overload
    def __call__(
        self, factory: Callable[[_ManagedLifeCycleT], Awaitable[_ServiceT]], /
    ) -> _AsynchronousServiceManager[_ManagedLifeCycleT, _ServiceT]:
        pass


@overload
def service(
    factory: Callable[[_ManagedLifeCycleT], Awaitable[_ServiceT]], /
) -> _AsynchronousServiceManager[_ManagedLifeCycleT, _ServiceT]:
    pass


@overload
def service(
    factory: Callable[[_ManagedLifeCycleT], _ServiceT], /
) -> _SynchronousServiceManager[_ManagedLifeCycleT, _ServiceT]:
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

    def _service(
        factory: Callable[[_ManagedLifeCycleT], _ServiceGetT], /
    ) -> ServiceManager[_ManagedLifeCycleT, _ServiceGetT, Any]:
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


@internal
class ServiceManager(Generic[_ManagedLifeCycleT, _ServiceGetT, _ServiceT]):
    """
    Manages a single service for a service container.
    """

    def __init__(
        self,
        factory: Intersection[
            ServiceFactory[_ManagedLifeCycleT, _ServiceGetT], FunctionType
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
    def __get__(self, instance: None, owner: type[_ManagedLifeCycleT]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: _ManagedLifeCycleT, owner: type[_ManagedLifeCycleT]
    ) -> _ServiceGetT:
        pass

    def __get__(
        self, instance: _ManagedLifeCycleT | None, owner: type[_ManagedLifeCycleT]
    ) -> _ServiceGetT | Self:
        if instance is None:
            return self

        return self.get(instance)

    def get(self, instance: _ManagedLifeCycleT, /) -> _ServiceGetT:
        """
        Get the service from an instance.
        """
        instance.assert_alive()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: _ManagedLifeCycleT, /) -> _ServiceGetT:
        pass

    def _get_attr(self, instance: _ManagedLifeCycleT, /) -> _ServiceT | Void:
        return getattr(instance, self._service_attr_name, Void())

    def _get_factory(
        self, instance: _ManagedLifeCycleT, /
    ) -> ServiceFactory[_ManagedLifeCycleT, _ServiceGetT]:
        factory = cast(
            "ServiceFactory[_ManagedLifeCycleT, _ServiceGetT] | None",
            getattr(instance, self._factory_override_attr_name, None),
        )
        if factory is not None:
            return factory
        return self._factory

    def _assert_not_initialized(self, instance: _ManagedLifeCycleT, /):
        if not isinstance(self._get_attr(instance), Void):
            raise ServiceInitializedError(
                f"{instance}.{self._service_name} was initialized already."
            )

    def override(self, instance: _ManagedLifeCycleT, service: _ServiceT, /) -> None:
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
        instance: _ManagedLifeCycleT,
        factory: ServiceFactory[_ManagedLifeCycleT, _ServiceGetT],
        /,
    ) -> None:
        """
        Override the default service factory for the given instance.

        This MUST only be called from ``instance.__init__()``. It will override the existing service factory method
        defined on the instance.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._factory_override_attr_name, factory)


class _AsynchronousServiceManager(
    Generic[_ManagedLifeCycleT, _ServiceT],
    ServiceManager[_ManagedLifeCycleT, Awaitable[_ServiceT], _ServiceT],
):
    def _lock(self, instance: _ManagedLifeCycleT, /) -> Lock:
        lock_attr_name = f"_{self._service_attr_name}_lock"
        try:
            return cast(Lock, getattr(instance, lock_attr_name))
        except AttributeError:
            lock = AsynchronizedLock.new_threadsafe()
            setattr(instance, lock_attr_name, lock)
            return lock

    @override
    async def _get(self, instance: _ManagedLifeCycleT, /) -> _ServiceT:
        async with self._lock(instance):
            service = self._get_attr(instance)

            if not isinstance(service, Void):
                return service

            new_service = await self._get_factory(instance)(instance)
            setattr(instance, self._service_attr_name, new_service)
            return new_service


class _SynchronousServiceManager(
    Generic[_ManagedLifeCycleT, _ServiceT],
    ServiceManager[_ManagedLifeCycleT, _ServiceT, _ServiceT],
):
    @override
    def _get(self, instance: _ManagedLifeCycleT, /) -> _ServiceT:
        service = self._get_attr(instance)
        if not isinstance(service, Void):
            return service

        new_service = self._get_factory(instance)(instance)
        setattr(instance, self._service_attr_name, new_service)
        return new_service


@internal
class ServiceInitializedError(ServiceError):
    """
    A service was unexpectedly initialized already.
    """
