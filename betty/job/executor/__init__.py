"""
Job execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, TypeVar

from betty.job import Context

if TYPE_CHECKING:
    from types import TracebackType

_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


class Executor(ABC):
    """
    A job executor.
    """

    @abstractmethod
    async def start(self) -> None:
        """
        Start working on jobs.
        """

    @abstractmethod
    async def cancel(self) -> None:
        """
        Stop the executor and cancel any pending jobs.
        """

    @abstractmethod
    async def complete(self) -> None:
        """
        Wait for any pending jobs to complete and stop the executor.
        """

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_val is None:
            await self.complete()
        else:
            await self.cancel()
