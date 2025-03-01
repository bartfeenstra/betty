"""
An API for providing application-wide services.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, MutableSequence, Awaitable
from inspect import iscoroutinefunction
from types import TracebackType
from typing import (
    Self,
    Any,
    final,
    TypedDict,
    Unpack,
    TypeAlias,
    cast,
    Generic,
)
from typing import overload, TypeVar
from warnings import warn

from typing_extensions import override

from betty.concurrent import AsynchronizedLock, Lock
from betty.typing import internal, public, Void, not_void, processsafe


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
            message = f"{self} was not bootstrapped yet."
            warn(message, stacklevel=2)
            raise RuntimeError(message)

    @final
    def assert_not_bootstrapped(self) -> None:
        """
        Assert that the component was not bootstrapped.
        """
        if self.bootstrapped:
            message = f"{self} was bootstrapped already."
            warn(message, stacklevel=2)
            raise RuntimeError(message)


class Shutdownable(ABC):
    """
    A component that can be shut down.
    """

    @abstractmethod
    async def shutdown(self, *, wait: bool = True) -> None:
        """
        Shut the component down.
        """
        pass


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

    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        self.assert_bootstrapped()
        self._bootstrapped = False
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


_ServiceProviderT = TypeVar("_ServiceProviderT", bound=ServiceProvider)
_ServiceT = TypeVar("_ServiceT")
_ServiceGetT = TypeVar("_ServiceGetT")

ServiceFactory: TypeAlias = Callable[[_ServiceProviderT], _ServiceT]


class _Service(Generic[_ServiceProviderT, _ServiceGetT, _ServiceT]):
    def __init__(self, factory: ServiceFactory[_ServiceProviderT, _ServiceGetT]):
        self._factory = factory
        self._service_name = factory.__name__  # type: ignore[attr-defined]
        self._attr_name = f"_{self._service_name}"
        self._explicit_attr_name = f"{self._attr_name}_explicit"
        self._factory_attr_name = f"{self._attr_name}_factory"

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

        instance.assert_bootstrapped()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: _ServiceProviderT) -> _ServiceGetT:
        pass

    def _get_attr(self, instance: _ServiceProviderT) -> _ServiceT | type[Void]:
        return getattr(instance, self._attr_name, Void)  # type: ignore[return-value]

    def _get_factory(
        self, instance: _ServiceProviderT
    ) -> ServiceFactory[_ServiceProviderT, _ServiceGetT]:
        factory = cast(
            ServiceFactory[_ServiceProviderT, _ServiceGetT] | None,
            getattr(instance, self._factory_attr_name, None),
        )
        if factory is not None:
            return factory
        return self._factory

    def _assert_not_initialized(self, instance: _ServiceProviderT):
        if not_void(self._get_attr(instance)):
            raise RuntimeError(
                f"{instance}.{self._service_name} was initialized already."
            )

    def init(self, instance: _ServiceProviderT, service: _ServiceT) -> None:
        """
        Explicitly initialize the service for the given instance.

        This MUST only be called from ``instance.__init__()``.

        The provided service MUST be pickleable.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._attr_name, service)
        setattr(instance, self._explicit_attr_name, True)

    def init_factory(
        self,
        instance: _ServiceProviderT,
        factory: ServiceFactory[_ServiceProviderT, _ServiceGetT],
    ) -> None:
        """
        Explicitly override the default service factory for the given instance.

        This MUST only be called from ``instance.__init__()``. It will override the existing service factory method
        defined on the instance.

        The provided factory MUST be pickleable.
        """
        self._assert_not_initialized(instance)
        setattr(instance, self._factory_attr_name, factory)


class _AsynchronousService(
    Generic[_ServiceProviderT, _ServiceT],
    _Service[_ServiceProviderT, Awaitable[_ServiceT], _ServiceT],
):
    def _lock(self, instance: _ServiceProviderT) -> Lock:
        lock_attr_name = f"_{self._attr_name}_lock"
        try:
            return cast(Lock, getattr(instance, lock_attr_name))
        except AttributeError:
            lock = AsynchronizedLock.threading()
            setattr(instance, lock_attr_name, lock)
            return lock

    async def _get(self, instance: _ServiceProviderT) -> _ServiceT:
        service = self._get_attr(instance)
        if not_void(service):
            return service

        async with self._lock(instance):
            new_service = await self._get_factory(instance)(instance)
            setattr(instance, self._attr_name, new_service)
            return new_service


class _SynchronousService(
    Generic[_ServiceProviderT, _ServiceT],
    _Service[_ServiceProviderT, _ServiceT, _ServiceT],
):
    def _get(self, instance: _ServiceProviderT) -> _ServiceT:
        service = self._get_attr(instance)
        if not_void(service):
            return service

        new_service = self._get_factory(instance)(instance)
        setattr(instance, self._attr_name, new_service)
        return new_service


@overload
def service(  # type: ignore[overload-overlap]
    factory: Callable[[_ServiceProviderT], Awaitable[_ServiceT]],
) -> _AsynchronousService[_ServiceProviderT, _ServiceT]:
    pass


@overload
def service(
    factory: Callable[[_ServiceProviderT], _ServiceT],
) -> _SynchronousService[_ServiceProviderT, _ServiceT]:
    pass


def service(
    factory: Callable[[_ServiceProviderT], _ServiceT],
) -> _Service[_ServiceProviderT, _ServiceT, Any]:
    """
    Decorate a service factory method.

    The decorated function should return a new service instance. The decorator will handle caching and concurrency.
    """
    if iscoroutinefunction(factory):
        return _AsynchronousService(factory)  # type: ignore[return-value]
    else:
        return _SynchronousService(factory)


@internal
@processsafe
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
