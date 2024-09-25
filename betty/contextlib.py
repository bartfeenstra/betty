"""
Provide context manager utilities.
"""

from types import TracebackType
from typing import AsyncContextManager, TypeVar, Generic

from betty.asyncio import wait_to_thread

_ContextT = TypeVar("_ContextT")


class SynchronizedContextManager(Generic[_ContextT]):
    """
    Make an asynchronous context manager synchronous.
    """

    def __init__(self, context_manager: AsyncContextManager[_ContextT]):
        self._context_manager = context_manager

    def __enter__(self) -> _ContextT:
        return wait_to_thread(self._context_manager.__aenter__)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return wait_to_thread(
            self._context_manager.__aexit__, exc_type, exc_val, exc_tb
        )
