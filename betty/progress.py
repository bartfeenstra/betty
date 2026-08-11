"""
Task progress management.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Self, final

if TYPE_CHECKING:
    from types import TracebackType


class Progress(metaclass=ABCMeta):
    """
    Track the progress of a number of tasks.

    This can be used as an asynchronous context manager, adding a task when entering, and marking it done when exiting.
    """

    @abstractmethod
    async def add(self, add: int = 1, /) -> None:
        """
        Add a number of tasks to the total.
        """

    @abstractmethod
    async def done(self, done: int = 1, /) -> None:
        """
        Mark a number of tasks done.
        """

    @final
    async def __aenter__(self) -> Self:
        await self.add()
        return self

    @final
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.done()
