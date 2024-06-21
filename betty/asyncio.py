"""
Provide asynchronous programming utilities.
"""

from __future__ import annotations

from asyncio import TaskGroup, run
from threading import Thread
from typing import (
    Awaitable,
    TypeVar,
    Generic,
    cast,
    ParamSpec,
    Coroutine,
    Any,
)

P = ParamSpec("P")
T = TypeVar("T")


async def gather(*coroutines: Coroutine[Any, None, T]) -> tuple[T, ...]:
    """
    Gather multiple coroutines.

    This is like Python's own ``asyncio.gather``, but with improved error handling.
    """
    tasks = []
    async with TaskGroup() as task_group:
        for coroutine in coroutines:
            tasks.append(task_group.create_task(coroutine))
    return tuple(task.result() for task in tasks)


def wait_to_thread(f: Awaitable[T]) -> T:
    """
    Wait for an awaitable in another thread.
    """
    synced = _WaiterThread(f)
    synced.start()
    synced.join()
    return synced.return_value


class _WaiterThread(Thread, Generic[T]):
    def __init__(self, awaitable: Awaitable[T]):
        super().__init__()
        self._awaitable = awaitable
        self._return_value: T | None = None
        self._e: BaseException | None = None

    @property
    def return_value(self) -> T:
        if self._e:
            raise self._e
        return cast(T, self._return_value)

    def run(self) -> None:
        run(self._run())

    async def _run(self) -> None:
        try:
            self._return_value = await self._awaitable
        except BaseException as e:  # noqa: B036
            # Store the exception, so it can be reraised when the calling thread
            # gets self.return_value.
            self._e = e
