from contextlib import AsyncExitStack
from types import TracebackType
from typing import Self, Any


class CoreComponent:
    def __init__(self, *args: Any, **kwargs: Any):
        self._bootstrapped = False
        self._exit_stack = AsyncExitStack()

    async def bootstrap(self) -> None:
        """
        Bootstrap the component.
        """
        if self._bootstrapped:
            raise RuntimeError(f"{self} was started already.")
        self._bootstrapped = True

    async def shutdown(self) -> None:
        """
        Shut the component down.
        """
        await self._exit_stack.aclose()
        self._bootstrapped = False

    def __del__(self) -> None:
        if self._bootstrapped:
            raise RuntimeError(f"{self} was bootstrapped, but never shut down.")

    async def __aenter__(self) -> Self:
        await self.bootstrap()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._exit_stack.aclose()
