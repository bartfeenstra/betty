"""
An API for providing application-wide services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterable, MutableSequence
from inspect import getmembers, iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    Self,
    TypeAlias,
    TypedDict,
    TypeVar,
    Unpack,
    cast,
    final,
    overload,
)
from warnings import warn

from typing_extensions import override

from betty.concurrent import AsynchronizedLock, Lock
from betty.config import Configurable
from betty.typing import Void, internal, public, unpickleable

if TYPE_CHECKING:
    from types import TracebackType


@internal
class ServiceError(RuntimeError):
    """
    A service API error.
    """


@internal
class BootstrappedError(ServiceError):
    """
    Something was unexpectedly bootstrapped already.
    """


@internal
class NotBootstrappedError(ServiceError):
    """
    Something was unexpectedly not yet bootstrapped.
    """


@internal
class ServiceInitializedError(ServiceError):
    """
    A service was unexpectedly initialized already.
    """


@internal
class Bootstrapped:
    """
    A component that can be in a bootstrapped state.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self._bootstrapped = False
        super().__init__(*args, **kwargs)

    @final
    @property
    def bootstrapped(self) -> bool:
        """
        Whether the component has been bootstrapped.
        """
        return self._bootstrapped

    @final
    def assert_bootstrapped(self) -> None:
        """
        Assert that the component has been bootstrapped.
        """
        if not self.bootstrapped:
            raise NotBootstrappedError(f"{self} was not bootstrapped yet.")

    @final
    def assert_not_bootstrapped(self) -> None:
        """
        Assert that the component was not bootstrapped.
        """
        if self.bootstrapped:
            raise BootstrappedError(f"{self} was bootstrapped already.")


class Shutdownable(ABC):
    """
    A component that can be shut down.
    """

    @abstractmethod
    async def shutdown(self, *, wait: bool = True) -> None:
        """
        Shut the component down.
        """


class ShutdownCallbackKwargs(TypedDict):
    """
    The keyword arguments to a shutdown callback.
    """

    #: ``True`` to wait for the component to shut down gracefully, or ``False`` to attempt an immediate forced shutdown.
    wait: bool


ShutdownCallback: TypeAlias = Callable[
    [Unpack[ShutdownCallbackKwargs]], Awaitable[None]
]


@internal
@final
class ShutdownStack(Bootstrapped, Shutdownable):
    """
    A stack that invokes callbacks in reverse order upon shutting down.
    """

    def __init__(self):
        super().__init__()
        self._bootstrapped = True
        self._callbacks: MutableSequence[ShutdownCallback] = []

    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        self.assert_bootstrapped()
        self._bootstrapped = False
        for callback in reversed(self._callbacks):
            await callback(wait=wait)

    def append(self, callback: ShutdownCallback | Shutdownable) -> None:
        """
        Append a callback or another component to the stack.
        """
        self._callbacks.append(
            callback.shutdown if isinstance(callback, Shutdownable) else callback
        )


@internal
@unpickleable
class ServiceProvider(Bootstrapped, Shutdownable):
    """
    A service provider.

    Service providers make up a running Betty 'application'. They can provide services through
    :py:func:`betty.service.service`, and manage their resources by being bootstrapped and shut down.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._shutdown_stack = ShutdownStack()

    @public
    async def bootstrap(self) -> None:
        """
        Bootstrap the component.
        """
        self.assert_not_bootstrapped()
        self._bootstrapped = True
        await self._bootstrap()

    async def _bootstrap(self) -> None:
        if isinstance(self, Configurable):
            self.configuration.immutable = True

    @classmethod
    def _service_managers(cls) -> Iterable[ServiceManager[Self, Any, Any]]:
        for _, value in getmembers(cls):
            if isinstance(value, ServiceManager):
                yield value

    @public
    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        self.assert_bootstrapped()
        self._bootstrapped = False
        await self._shutdown(wait=wait)

    async def _shutdown(self, *, wait: bool = True) -> None:
        await self._shutdown_stack.shutdown(wait=wait)
        if isinstance(self, Configurable):
            self.configuration.mutable = True

    def __del__(self) -> None:
        if self.bootstrapped:
            warn(f"{self} was bootstrapped, but never shut down.", stacklevel=2)

    @public
    @final
    async def __aenter__(self) -> Self:
        await self.bootstrap()
        return self

    @public
    @final
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.shutdown(wait=exc_val is None)


_ServiceProviderT = TypeVar("_ServiceProviderT", bound=ServiceProvider)
_ServiceT = TypeVar("_ServiceT")
_ServiceGetT = TypeVar("_ServiceGetT")

ServiceFactory: TypeAlias = Callable[[_ServiceProviderT], _ServiceT]


@internal
class ServiceManager(Generic[_ServiceProviderT, _ServiceGetT, _ServiceT]):
    """
    Manages a single service for a service provider.
    """

    def __init__(self, factory: ServiceFactory[_ServiceProviderT, _ServiceGetT]):
        self._factory = factory
        self._service_name: str = factory.__name__  # type: ignore[attr-defined]
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
    def __get__(self, instance: None, owner: type[_ServiceProviderT]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: _ServiceProviderT, owner: type[_ServiceProviderT]
    ) -> _ServiceGetT:
        pass

    def __get__(
        self, instance: _ServiceProviderT | None, owner: type[_ServiceProviderT]
    ) -> _ServiceGetT | Self:
        if instance is None:
            return self  # type: ignore[return-value]

        return self.get(instance)

    def get(self, instance: _ServiceProviderT) -> _ServiceGetT:
        """
        Get the service from an instance.
        """
        instance.assert_bootstrapped()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: _ServiceProviderT) -> _ServiceGetT:
        pass

    def _get_attr(self, instance: _ServiceProviderT) -> _ServiceT | Void:
        return getattr(instance, self._service_attr_name, Void())  # type: ignore[return-value]

    def _get_factory(
        self, instance: _ServiceProviderT
    ) -> ServiceFactory[_ServiceProviderT, _ServiceGetT]:
        factory = cast(
            "ServiceFactory[_ServiceProviderT, _ServiceGetT] | None",
            getattr(instance, self._factory_override_attr_name, None),
        )
        if factory is not None:
            return factory
        return self._factory

    def _assert_not_initialized(self, instance: _ServiceProviderT):
        if not isinstance(self._get_attr(instance), Void):
            raise ServiceInitializedError(
                f"{instance}.{self._service_name} was initialized already."
            )

    def override(self, instance: _ServiceProviderT, service: _ServiceT) -> None:
        """
        Override the service for the given instance.

        Calling this will prevent any existing factory from being called.

        This MUST only be called from ``instance.__init__()``.

        The provided service MUST be pickleable.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._service_attr_name, service)
        setattr(instance, self._service_override_attr_name, True)

    def override_factory(
        self,
        instance: _ServiceProviderT,
        factory: ServiceFactory[_ServiceProviderT, _ServiceGetT],
    ) -> None:
        """
        Override the default service factory for the given instance.

        This MUST only be called from ``instance.__init__()``. It will override the existing service factory method
        defined on the instance.

        The provided factory MUST be pickleable.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._factory_override_attr_name, factory)


class _AsynchronousServiceManager(
    Generic[_ServiceProviderT, _ServiceT],
    ServiceManager[_ServiceProviderT, Awaitable[_ServiceT], _ServiceT],
):
    def _lock(self, instance: _ServiceProviderT) -> Lock:
        lock_attr_name = f"_{self._service_attr_name}_lock"
        try:
            return cast(Lock, getattr(instance, lock_attr_name))
        except AttributeError:
            lock = AsynchronizedLock.new_threadsafe()
            setattr(instance, lock_attr_name, lock)
            return lock

    @override
    async def _get(self, instance: _ServiceProviderT) -> _ServiceT:
        async with self._lock(instance):
            service = self._get_attr(instance)

            if not isinstance(service, Void):
                return service

            new_service = await self._get_factory(instance)(instance)
            setattr(instance, self._service_attr_name, new_service)
            return new_service


class _SynchronousServiceManager(
    Generic[_ServiceProviderT, _ServiceT],
    ServiceManager[_ServiceProviderT, _ServiceT, _ServiceT],
):
    @override
    def _get(self, instance: _ServiceProviderT) -> _ServiceT:
        service = self._get_attr(instance)
        if not isinstance(service, Void):
            return service

        new_service = self._get_factory(instance)(instance)
        setattr(instance, self._service_attr_name, new_service)
        return new_service


class _ServiceDecorator(Protocol):
    @overload
    def __call__(
        self, factory: Callable[[_ServiceProviderT], _ServiceT]
    ) -> _SynchronousServiceManager[_ServiceProviderT, _ServiceT]:
        pass

    @overload
    def __call__(
        self, factory: Callable[[_ServiceProviderT], Awaitable[_ServiceT]]
    ) -> _AsynchronousServiceManager[_ServiceProviderT, _ServiceT]:
        pass


@overload
def service(  # type: ignore[overload-overlap]
    factory: Callable[[_ServiceProviderT], Awaitable[_ServiceT]],
) -> _AsynchronousServiceManager[_ServiceProviderT, _ServiceT]:
    pass


@overload
def service(
    factory: Callable[[_ServiceProviderT], _ServiceT],
) -> _SynchronousServiceManager[_ServiceProviderT, _ServiceT]:
    pass


@overload
def service(factory: None = None) -> _ServiceDecorator:
    pass


def service(
    factory: Callable[[_ServiceProviderT], _ServiceGetT] | None = None,
) -> ServiceManager[_ServiceProviderT, _ServiceGetT, Any] | _ServiceDecorator:
    """
    Decorate a service factory method.

    The factory method is replaced with a :py:class:`service manager <betty.service.ServiceManager>` which handles lazy
    service instantiation, caching, and multiprocessing support.

    The decorated factory method should return a new service instance.
    """

    def _service(
        factory: Callable[[_ServiceProviderT], _ServiceGetT],
    ) -> ServiceManager[_ServiceProviderT, _ServiceGetT, Any]:
        if iscoroutinefunction(factory):
            return _AsynchronousServiceManager(factory)  # type: ignore[return-value]
        return _SynchronousServiceManager(factory)

    if factory is None:
        return _service  # type: ignore[return-value]
    return _service(factory)


@internal
class StaticService(Generic[_ServiceProviderT, _ServiceT]):
    """
    A service factory that returns a static, predefined service.
    """

    def __init__(self, service: _ServiceT):
        self._service = service

    def __call__(self, service_provider: _ServiceProviderT) -> _ServiceT:
        """
        Return the service.
        """
        return self._service
