import asyncio
import inspect
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
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(f)
        synced = _SyncedAwaitable(f)
        synced.start()
        synced.join()
        return synced.return_value

    if inspect.iscoroutinefunction(f):
        return _sync_function(f)

    if callable(f):
        with suppress(AttributeError):
            if inspect.iscoroutinefunction(getattr(f, '__call__')):
                return _sync_function(f)
        return f

    raise ValueError('Can only synchronize coroutine callables (`async def`) or coroutines (values returned by `async def`), or pass through synchronous callables, but "%s" was given.' % f)


class _SyncedAwaitable(Thread):
    def __init__(self, awaitable):
        super().__init__()
        self._awaitable = awaitable
        self._return_value = None

    @property
    def return_value(self) -> Any:
        return self._return_value

    @sync
    async def run(self) -> None:
        self._return_value = await self._awaitable
