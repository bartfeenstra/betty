"""
Provide asynchronous programming utilities.
"""

from __future__ import annotations

from asyncio import TaskGroup, get_running_loop, run
from functools import wraps
from threading import Thread
from typing import (
    Callable,
    Awaitable,
    TypeVar,
    Generic,
    cast,
    ParamSpec,
    Coroutine,
    Any,
)

from betty.warnings import deprecated

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


@deprecated(
    "This function is deprecated as of Betty 0.3.3, and will be removed in Betty 0.4.x. Instead, use `betty.asyncio.wait_to_thread()` or `asyncio.run()`."
)
def wait(f: Awaitable[T]) -> T:
    """
    Wait for an awaitable, either in a new event loop or another thread.
    """
    try:
        loop = get_running_loop()
    except RuntimeError:
        loop = None
    if loop:
        return wait_to_thread(f)
    else:
        return run(
            f,  # type: ignore[arg-type]
        )


def wait_to_thread(f: Awaitable[T]) -> T:
    """
    Wait for an awaitable in another thread.
    """
    synced = _WaiterThread(f)
    synced.start()
    synced.join()
    return synced.return_value


@deprecated(
    "This function is deprecated as of Betty 0.3.3, and will be removed in Betty 0.4.x. Instead, use `betty.asyncio.wait_to_thread()` or `asyncio.run()`."
)
def sync(f: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    """
    Decorate an asynchronous callable to become synchronous.
    """

    @wraps(f)
    def _synced(*args: P.args, **kwargs: P.kwargs) -> T:
        return wait(f(*args, **kwargs))

    return _synced


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
