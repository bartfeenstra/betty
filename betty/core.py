"""
Provide tools to build core application components.
"""

from abc import ABC
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Self, Any
from warnings import warn

from betty.typing import internal, public


@internal
class CoreComponent(ABC):  # noqa B024
    """
    A core component.

    Core components can manage their resources by being bootstrapped and shut down.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._bootstrapped = False
        self._async_exit_stack = AsyncExitStack()

    @property
    def bootstrapped(self) -> bool:
        """
        Whether the component has been bootstrapped.
        """
        return self._bootstrapped

    @public
    def assert_bootstrapped(self) -> None:
        """
        Assert that the component has been bootstrapped.
        """
        if not self.bootstrapped:
            message = f"{self} was not bootstrapped yet."
            warn(message, stacklevel=2)
            raise RuntimeError(message)

    @public
    def assert_not_bootstrapped(self) -> None:
        """
        Assert that the component was not bootstrapped.
        """
        if self.bootstrapped:
            message = f"{self} was bootstrapped already."
            warn(message, stacklevel=2)
            raise RuntimeError(message)

    @public
    async def bootstrap(self) -> None:
        """
        Bootstrap the component.
        """
        self.assert_not_bootstrapped()
        self._bootstrapped = True

    @public
    async def shutdown(self) -> None:
        """
        Shut the component down.
        """
        self.assert_bootstrapped()
        await self._async_exit_stack.aclose()
        self._bootstrapped = False

    def __del__(self) -> None:
        if self.bootstrapped:
            warn(f"{self} was bootstrapped, but never shut down.", stacklevel=2)

    async def __aenter__(self) -> Self:
        await self.bootstrap()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.shutdown()
