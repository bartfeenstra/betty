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
    Coroutine,
    Any,
    ParamSpec,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from collections.abc import Callable


_T = TypeVar("_T")
_U = TypeVar("_U")
_V = TypeVar("_V")


async def gather(*coroutines: Coroutine[Any, None, _T]) -> tuple[_T, ...]:
    """
    Gather multiple coroutines.

    This is like Python's own ``asyncio.gather``, but with improved error handling.
    """
    tasks = []
    async with TaskGroup() as task_group:
        for coroutine in coroutines:
            tasks.append(task_group.create_task(coroutine))
    return tuple(task.result() for task in tasks)


def wait_to_thread(f: Awaitable[_T]) -> _T:
    """
    Wait for an awaitable in another thread.
    """
    synced = _WaiterThread(f)
    synced.start()
    synced.join()
    return synced.return_value


class _WaiterThread(Thread, Generic[_T]):
    def __init__(self, awaitable: Awaitable[_T]):
        super().__init__()
        self._awaitable = awaitable
        self._return_value: _T | None = None
        self._e: BaseException | None = None

    @property
    def return_value(self) -> _T:
        if self._e:
            raise self._e
        return cast(_T, self._return_value)

    def run(self) -> None:
        run(self._run())

    async def _run(self) -> None:
        try:
            self._return_value = await self._awaitable
        except BaseException as e:  # noqa: B036
            # Store the exception, so it can be reraised when the calling thread
            # gets self.return_value.
            self._e = e


_P = ParamSpec("_P")


def make_async(f: Callable[_P, _T]) -> Callable[_P, Awaitable[_T]]:
    """
    Make the given callable asynchronous.

    The returned callable will have an identical signature, except that the return value
    will be wrapped in an awaitable.
    """

    async def _make_async(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        return f(*args, **kwargs)

    return _make_async
