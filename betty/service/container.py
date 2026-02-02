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
    final,
    overload,
)
from warnings import warn

from typing_extensions import override

from betty.concurrent import AsynchronizedLock, Lock
from betty.service import ServiceError
from betty.service.bootstrap import Bootstrapped, Shutdownable, ShutdownStack
from betty.typing import Void, internal

if TYPE_CHECKING:
    from types import FunctionType, TracebackType

    from ty_extensions import Intersection

    from betty.service.level import ServiceLevel


_T = TypeVar("_T")
_ServiceT = TypeVar("_ServiceT")
_ServiceGetT = TypeVar("_ServiceGetT")


# @todo Do we need this still?
# @todo
# @todo
class ServiceContainer:
    """
    A service container.

    Service containers make up a running Betty 'application'. They can provide services through
    :py:func:`betty.service.container.service`, and manage their resources by being bootstrapped and shut down.
    """


class EphemeralServiceContainer(Bootstrapped, Shutdownable, ServiceContainer):
    def __init__(self, *args: Any, services: ServiceLevel, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._services = services
        self._shutdown_stack = ShutdownStack()

    async def bootstrap(self) -> None:
        """
        Bootstrap the component.
        """
        self.assert_not_bootstrapped()
        self._bootstrapped = True
        await self._bootstrap()
        await self._post_bootstrap()

    async def _bootstrap(self) -> None:
        pass

    async def _post_bootstrap(self) -> None:
        from betty.config import Configurable

        if isinstance(self, Configurable):
            await self.configuration.data().hydrate(
                services=self._services, data=self.configuration
            )

    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        self.assert_bootstrapped()
        self._bootstrapped = False
        await self._shutdown(wait=wait)

    async def _shutdown(self, *, wait: bool = True) -> None:
        await self._shutdown_stack.shutdown(wait=wait)

    def __del__(self) -> None:
        if self.bootstrapped:
            warn(f"{self} was bootstrapped, but never shut down.", stacklevel=2)

    @final
    async def __aenter__(self) -> Self:
        await self.bootstrap()
        return self

    @final
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.shutdown(wait=exc_val is None)


_ServiceContainerT = TypeVar("_ServiceContainerT", bound=ServiceContainer)


ServiceFactory: TypeAlias = Callable[[_ServiceContainerT], _ServiceT]


class _ServiceDecorator(Protocol):
    @overload
    def __call__(
        self, factory: Callable[[_ServiceContainerT], _ServiceT], /
    ) -> _SynchronousServiceManager[_ServiceContainerT, _ServiceT]:
        pass

    @overload
    def __call__(
        self, factory: Callable[[_ServiceContainerT], Awaitable[_ServiceT]], /
    ) -> _AsynchronousServiceManager[_ServiceContainerT, _ServiceT]:
        pass


@overload
def service(
    factory: Callable[[_ServiceContainerT], Awaitable[_ServiceT]], /
) -> _AsynchronousServiceManager[_ServiceContainerT, _ServiceT]:
    pass


@overload
def service(
    factory: Callable[[_ServiceContainerT], _ServiceT], /
) -> _SynchronousServiceManager[_ServiceContainerT, _ServiceT]:
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
        factory: Callable[[_ServiceContainerT], _ServiceGetT], /
    ) -> ServiceManager[_ServiceContainerT, _ServiceGetT, Any]:
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
class StaticService(Generic[_ServiceContainerT, _ServiceT]):
    """
    A service factory that returns a static, predefined service.
    """

    def __init__(self, service: _ServiceT, /):
        self._service = service

    def __call__(self, services: _ServiceContainerT, /) -> _ServiceT:
        """
        Return the service.
        """
        return self._service


@internal
class ServiceManager(Generic[_ServiceContainerT, _ServiceGetT, _ServiceT]):
    """
    Manages a single service for a service container.
    """

    def __init__(
        self,
        factory: Intersection[
            # @todo If we use __set_name__(), we can accept more types than just functions.
            # @todo
            # @todo
            ServiceFactory[_ServiceContainerT, _ServiceGetT], FunctionType
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
    def __get__(self, instance: None, owner: type[_ServiceContainerT]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: _ServiceContainerT, owner: type[_ServiceContainerT]
    ) -> _ServiceGetT:
        pass

    def __get__(
        self, instance: _ServiceContainerT | None, owner: type[_ServiceContainerT]
    ) -> _ServiceGetT | Self:
        if instance is None:
            return self

        return self.get(instance)

    def get(self, instance: _ServiceContainerT, /) -> _ServiceGetT:
        """
        Get the service from an instance.
        """
        if isinstance(instance, EphemeralServiceContainer):
            instance.assert_bootstrapped()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: _ServiceContainerT, /) -> _ServiceGetT:
        pass

    def _get_attr(self, instance: _ServiceContainerT, /) -> _ServiceT | Void:
        return getattr(instance, self._service_attr_name, Void())

    def _get_factory(
        self, instance: _ServiceContainerT, /
    ) -> ServiceFactory[_ServiceContainerT, _ServiceGetT]:
        factory = cast(
            "ServiceFactory[_ServiceContainerT, _ServiceGetT] | None",
            getattr(instance, self._factory_override_attr_name, None),
        )
        if factory is not None:
            return factory
        return self._factory

    def _assert_not_initialized(self, instance: _ServiceContainerT, /):
        if not isinstance(self._get_attr(instance), Void):
            raise ServiceInitializedError(
                f"{instance}.{self._service_name} was initialized already."
            )

    def override(self, instance: _ServiceContainerT, service: _ServiceT, /) -> None:
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
        instance: _ServiceContainerT,
        factory: ServiceFactory[_ServiceContainerT, _ServiceGetT],
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
    Generic[_ServiceContainerT, _ServiceT],
    ServiceManager[_ServiceContainerT, Awaitable[_ServiceT], _ServiceT],
):
    def _lock(self, instance: _ServiceContainerT, /) -> Lock:
        lock_attr_name = f"_{self._service_attr_name}_lock"
        try:
            return cast(Lock, getattr(instance, lock_attr_name))
        except AttributeError:
            lock = AsynchronizedLock.new_threadsafe()
            setattr(instance, lock_attr_name, lock)
            return lock

    @override
    async def _get(self, instance: _ServiceContainerT, /) -> _ServiceT:
        async with self._lock(instance):
            service = self._get_attr(instance)

            if not isinstance(service, Void):
                return service

            new_service = await self._get_factory(instance)(instance)
            setattr(instance, self._service_attr_name, new_service)
            return new_service


class _SynchronousServiceManager(
    Generic[_ServiceContainerT, _ServiceT],
    ServiceManager[_ServiceContainerT, _ServiceT, _ServiceT],
):
    @override
    def _get(self, instance: _ServiceContainerT, /) -> _ServiceT:
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
