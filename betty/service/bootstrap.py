"""
Components that can be bootstrapped and shut down.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, MutableSequence
from typing import Any, TypeAlias, TypedDict, Unpack, final

from typing_extensions import override

from betty.service import ServiceError
from betty.typing import internal


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

    wait: bool
    """
    ``True`` to wait for the component to shut down gracefully, or ``False`` to attempt an immediate forced shutdown.
    """


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

    def append(self, callback: ShutdownCallback | Shutdownable, /) -> None:
        """
        Append a callback or another component to the stack.
        """
        self._callbacks.append(
            callback.shutdown if isinstance(callback, Shutdownable) else callback
        )
