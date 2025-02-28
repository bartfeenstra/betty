"""
Provide tools to build core application components.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, MutableSequence, Awaitable
from inspect import iscoroutinefunction
from types import TracebackType
from typing import Self, Any, final, TypedDict, Unpack, TypeAlias, cast, Generic
from typing import overload, TypeVar
from warnings import warn

from typing_extensions import override

from betty.concurrent import AsynchronizedLock, Lock
from betty.typing import internal, public

_T = TypeVar("_T")


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
class CoreComponent(Bootstrapped, Shutdownable):
    """
    A core component.

    Core components can manage their resources by being bootstrapped and shut down.
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


_CoreComponentT = TypeVar("_CoreComponentT", bound=CoreComponent)


class _Service(Generic[_CoreComponentT, _T]):
    def __init__(self, f: Callable[[_CoreComponentT], _T]):
        self._f = f
        f_name = f.__name__  # type: ignore[attr-defined]
        self._attr_name = f"_{f_name}"

    @overload
    def __get__(self, instance: None, owner: type[_CoreComponentT]) -> Self:
        pass

    @overload
    def __get__(self, instance: _CoreComponentT, owner: type[_CoreComponentT]) -> _T:
        pass

    def __get__(
        self, instance: _CoreComponentT | None, owner: type[_CoreComponentT]
    ) -> _T | Self:
        if instance is None:
            return self  # type: ignore[return-value]

        instance.assert_bootstrapped()

        return self._get(instance)

    @abstractmethod
    def _get(self, instance: _CoreComponentT) -> _T:
        pass


class _AsynchronousService(_Service[_CoreComponentT, Awaitable[_T]]):
    async def _get(self, instance: _CoreComponentT) -> _T:
        service = cast(_T | None, getattr(instance, self._attr_name, None))
        if service is not None:
            return service

        lock_attr_name = f"_{self._attr_name}_lock"
        try:
            lock = cast(Lock, getattr(instance, lock_attr_name))
        except AttributeError:
            lock = AsynchronizedLock.threading()
            setattr(instance, lock_attr_name, lock)
        async with lock:
            service = await self._f(instance)
            setattr(instance, self._attr_name, service)
            return service


class _SynchronousService(_Service[_CoreComponentT, _T]):
    def _get(self, instance: _CoreComponentT) -> _T:
        service = cast(_T | None, getattr(instance, self._attr_name, None))
        if service is not None:
            return service

        service = self._f(instance)
        setattr(instance, self._attr_name, service)
        return service


def service(f: Callable[[_CoreComponentT], _T]) -> _Service[_CoreComponentT, _T]:
    """
    Decorate a :py:class:`betty.core.CoreComponent`'s method to be a service property.

    The decorated function should return a new service instance. The decorator will handle caching and concurrency.
    """
    if iscoroutinefunction(f):
        return _AsynchronousService(f)  # type: ignore[return-value]
    else:
        return _SynchronousService(f)
