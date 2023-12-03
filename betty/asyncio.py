from __future__ import annotations

import asyncio
from asyncio import TaskGroup
from contextlib import AbstractAsyncContextManager
from functools import wraps
from threading import Thread
from typing import Callable, Awaitable, TypeVar, Generic, cast, ParamSpec, Coroutine, Any, Self

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
        self._error: BaseException | None = None

    @property
    def return_value(self) -> T:
        if self._error:
            raise self._error
        return cast(T, self._return_value)

    @sync
    async def run(self) -> None:
        try:
            self._return_value = await self._awaitable
        except BaseException as error:
            self._error = error


class ConcurrentExitStack:
    def __init__(self):
        self._stack = []

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await gather(*(
            frame.__aexit__(exc_type, exc_val, exc_tb)
            for frame
            in self._stack
        ))

    async def exit(self) -> None:
        await self.__aexit__(None, None, None)

    async def add(self, *context_managers: AbstractAsyncContextManager[Any]) -> None:
        await gather(*(
            self._add_one(context_manager)
            for context_manager
            in context_managers
        ))

    async def _add_one(self, context_manager: AbstractAsyncContextManager[Any]) -> None:
        await context_manager.__aenter__()
        self._stack.append(context_manager)
