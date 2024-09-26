"""
Provide asynchronous programming utilities.
"""

from __future__ import annotations

from asyncio import TaskGroup, get_running_loop, run_coroutine_threadsafe
from concurrent.futures import wait
from threading import Thread
from typing import (
    Awaitable,
    TypeVar,
    Generic,
    Coroutine,
    Any,
    ParamSpec,
    TYPE_CHECKING,
    cast,
)
from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Callable

_T = TypeVar("_T")
_P = ParamSpec("_P")


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


def wait_to_thread(
    f: Callable[_P, Awaitable[_T]], *args: _P.args, **kwargs: _P.kwargs
) -> _T:
    synced = _WaiterThread(f, *args, **kwargs)
    synced.start()
    synced.join()
    return synced.return_value


class _WaiterThread(Thread, Generic[_T]):
    def __init__(
        self, f: Callable[_P, Awaitable[_T]], *args: _P.args, **kwargs: _P.kwargs
    ):
        super().__init__()
        self._loop = get_running_loop()
        self._f = f
        self._args = args
        self._kwargs = kwargs
        self._return_value: _T | None = None
        self._e: BaseException | None = None

    @property
    def return_value(self) -> _T:
        if self._e:
            raise self._e
        return cast(_T, self._return_value)

    @override
    def run(self) -> None:
        try:
            future = run_coroutine_threadsafe(
                self._f(*self._args, **self._kwargs), self._loop
            )
            wait([future])
            self._return_value = future.result()
            foo()
        except BaseException as e:  # noqa: B036
            # Store the exception, so it can be reraised when the calling thread
            # gets self.return_value.
            self._e = e
