from __future__ import annotations

import asyncio
from asyncio import TaskGroup
from functools import wraps
from threading import Thread
from typing import Callable, Awaitable, TypeVar, Generic, cast, ParamSpec, Coroutine, Any

P = ParamSpec('P')
T = TypeVar('T')


async def gather(*coroutines: Coroutine[Any, None, T]) -> tuple[T, ...]:
    tasks = []
    async with TaskGroup() as task_group:
        for coroutine in coroutines:
            tasks.append(task_group.create_task(coroutine))
    return tuple(
        task.result()
        for task
        in tasks
    )


def wait(f: Awaitable[T]) -> T:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop:
        synced = _SyncedAwaitable(f)
        synced.start()
        synced.join()
        return synced.return_value
    else:
        return asyncio.run(
            f,  # type: ignore[arg-type]
        )


def sync(f: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    @wraps(f)
    def _synced(*args: P.args, **kwargs: P.kwargs) -> T:
        return wait(f(*args, **kwargs))
    return _synced


class _SyncedAwaitable(Thread, Generic[T]):
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

    @sync
    async def run(self) -> None:
        try:
            self._return_value = await self._awaitable
        except BaseException as e:
            self._e = e
