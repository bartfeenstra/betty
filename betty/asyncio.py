import asyncio
import inspect
import sys
from asyncio import events, coroutines
from asyncio.runners import _cancel_all_tasks  # type: ignore
from contextlib import suppress
from functools import wraps
from threading import Thread
from typing import Any


def _sync_function(f):
    @wraps(f)
    def _synced(*args, **kwargs):
        return sync(f(*args, **kwargs))
    return _synced


def sync(f):
    if inspect.iscoroutine(f):
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop:
            synced = _SyncedAwaitable(f)
            synced.start()
            return synced.join()

        return _run(f)

    if inspect.iscoroutinefunction(f):
        return _sync_function(f)

    if callable(f):
        with suppress(AttributeError):
            if inspect.iscoroutinefunction(getattr(f, '__call__')):
                return _sync_function(f)
        return f

    raise ValueError('Can only synchronize coroutine callables (`async def`) or coroutines (values returned by `async def`), or pass through synchronous callables, but "%s" was given.' % f)


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


class _SyncedAwaitable(Thread):
    def __init__(self, awaitable):
        super().__init__()
        self._awaitable = awaitable
        self._return_value = None
        self._e = None

    @sync
    async def run(self) -> None:
        try:
            self._return_value = await self._awaitable
        except BaseException as e:
            self._e = e

    def join(self, *args, **kwargs) -> Any:
        super().join(*args, **kwargs)
        if self._e:
            raise self._e
        return self._return_value
