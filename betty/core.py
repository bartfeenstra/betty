"""
Provide tools to build core application components.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, MutableSequence, Awaitable
from types import TracebackType
from typing import Self, Any, final, TypedDict, Unpack, TypeAlias
from warnings import warn

from typing_extensions import override

from betty.typing import internal, public


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
class CoreComponent(Bootstrapped, Shutdownable, ABC):  # noqa B024
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
