from __future__ import annotations

import asyncio
import sys
from asyncio import events, coroutines
from asyncio.runners import _cancel_all_tasks  # type: ignore
from functools import wraps
from threading import Thread
from typing import Callable, Awaitable, TypeVar, Generic, cast

try:
    from typing_extensions import ParamSpec
except ModuleNotFoundError:
    from typing import ParamSpec  # type: ignore


P = ParamSpec('P')
T = TypeVar('T')


def wait(f: Awaitable[T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run(f)
    else:
        synced = _SyncedAwaitable(f)
        synced.start()
        synced.join()
        return synced.return_value


def sync(f: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    @wraps(f)
    def _synced(*args, **kwargs):
        return wait(f(*args, **kwargs))
    return _synced


def _run(main, *, debug=None):
    """
    A verbatim copy of asyncio.run(), with some improvements.
    """
    if events._get_running_loop() is not None:
        raise RuntimeError("asyncio.run() cannot be called from a running event loop")

    if not coroutines.iscoroutine(main):
        raise ValueError("a coroutine was expected, got {!r}".format(main))

    loop = events.new_event_loop()
    try:
        events.set_event_loop(loop)
        if debug is not None:
            loop.set_debug(debug)
        return loop.run_until_complete(main)
    finally:
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            # Improvement: Python 3.9 added the ability to shut down the default executor.
            if sys.version_info.minor >= 9:
                loop.run_until_complete(
                    loop.shutdown_default_executor()  # type: ignore
                )
        finally:
            events.set_event_loop(None)
            loop.close()


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
