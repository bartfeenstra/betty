"""
Provide context manager utilities.
"""
from types import TracebackType
from typing import AsyncContextManager, TypeVar, Generic

from betty.asyncio import wait_to_thread

ContextT = TypeVar('ContextT')


class SynchronizedContextManager(Generic[ContextT]):
    def __init__(self, context_manager: AsyncContextManager[ContextT]):
        self._context_manager = context_manager

    def __enter__(self) -> ContextT:
        return wait_to_thread(self._context_manager.__aenter__())

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool | None:
        return wait_to_thread(self._context_manager.__aexit__(exc_type, exc_val, exc_tb))
