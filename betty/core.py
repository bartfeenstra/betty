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

    @public
    def _assert_bootstrapped(self) -> None:
        if not self._bootstrapped:
            message = f"{self} was not bootstrapped yet."
            warn(message, stacklevel=2)
            raise RuntimeError(message)

    @public
    def _assert_not_yet_bootstrapped(self) -> None:
        if self._bootstrapped:
            message = f"{self} was bootstrapped already."
            warn(message, stacklevel=2)
            raise RuntimeError(message)

    @public
    async def bootstrap(self) -> None:
        """
        Bootstrap the component.
        """
        self._assert_not_yet_bootstrapped()
        self._bootstrapped = True

    @public
    async def shutdown(self) -> None:
        """
        Shut the component down.
        """
        self._assert_bootstrapped()
        await self._async_exit_stack.aclose()
        self._bootstrapped = False

    def __del__(self) -> None:
        if self._bootstrapped:
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
