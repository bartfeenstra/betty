"""
Life cycle and resource management.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol, Self, final
from warnings import warn

if TYPE_CHECKING:
    from types import TracebackType

    from betty.asyncio import ResolvableAwaitable


class LifeCycleError(RuntimeError):
    """
    Raised for life cycle related errors.
    """


class NotYetBootstrapped(LifeCycleError):
    """
    Raised if a life cycle was unexpectedly not yet bootstrapped.
    """


class AlreadyBootstrapped(LifeCycleError):
    """
    Raised if a life cycle was unexpectedly already bootstrapped.
    """


class AlreadyShutDown(AlreadyBootstrapped):
    """
    Raised if a life cycle was unexpectedly already shut down.
    """


class _LifeCycleContextManager:
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass


class Bootstrappable(_LifeCycleContextManager):
    """
    An object that can be bootstrapped.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.__bootstrapped = False
        super().__init__(*args, **kwargs)

    @final
    @property
    def bootstrapped(self) -> bool:
        """
        Whether the object has been bootstrapped.
        """
        return self.__bootstrapped

    @final
    def assert_not_bootstrapped(self) -> None:
        """
        Assert that the object is not yet bootstrapped.
        """
        if self.bootstrapped:
            raise AlreadyBootstrapped(f"{self} was bootstrapped already.")

    @final
    def assert_bootstrapped(self) -> None:
        """
        Assert that the object is bootstrapped.
        """
        if not self.bootstrapped:
            raise NotYetBootstrapped(f"{self} was not bootstrapped yet.")

    async def bootstrap(self) -> None:
        """
        Bootstrap the object.
        """
        self.assert_not_bootstrapped()
        self.__bootstrapped = True

    @final
    async def __aenter__(self) -> Self:
        await self.bootstrap()
        return self


class Shutdownable(_LifeCycleContextManager):
    """
    An object that can be shut down.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.__shut_down = False
        super().__init__(*args, **kwargs)

    @final
    @property
    def shut_down(self) -> bool:
        """
        Whether the object has been shut down.
        """
        return self.__shut_down

    @final
    def assert_not_shut_down(self) -> None:
        """
        Assert that the object is not yet shut down.
        """
        if self.shut_down:
            raise AlreadyShutDown(f"{self} was shut down already.")

    async def shutdown(self, *, wait: bool = True) -> None:
        """
        Shut the object down.
        """
        if self.__shut_down and not wait:
            return
        self.assert_not_shut_down()
        self.__shut_down = True

    @final
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.shutdown(wait=exc_val is None)

    def __del__(self) -> None:
        if not self.__shut_down:
            warn(f"{self} was never shut down.", stacklevel=2)


class LifeCycle(Bootstrappable, Shutdownable):
    """
    An object that can be bootstrapped and shut down.
    """

    @final
    @property
    def alive(self) -> bool:
        """
        Whether the object is alive, e.g. bootstrapped but not shut down.
        """
        return self.bootstrapped and not self.shut_down

    @final
    def assert_alive(self) -> None:
        """
        Assert that the object is alive, e.g. bootstrapped but not shut down.
        """
        self.assert_bootstrapped()
        self.assert_not_shut_down()

    def __del__(self) -> None:
        if self.alive:
            warn(f"{self} was bootstrapped, but never shut down.", stacklevel=2)


type Bootstrapper = Callable[[], Awaitable[None] | None]
"""
A callback to bootstrap resources.
"""


class Shutdowner(Protocol):
    """
    A callback to shut down resources.
    """

    def __call__(self, *, wait: bool) -> ResolvableAwaitable[None]:
        """
        Shut down resources.
        """
