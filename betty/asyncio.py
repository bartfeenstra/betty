import asyncio
import inspect
from contextlib import suppress
from functools import wraps


def _wrap_sync(f):
    @wraps(f)
    def _synced(*args, **kwargs):
        return sync(f(*args, **kwargs))
    return _synced


def sync(f):
    if inspect.iscoroutine(f):
        return asyncio.get_event_loop().run_until_complete(f)

    if inspect.iscoroutinefunction(f):
        return _wrap_sync(f)

    if callable(f):
        with suppress(AttributeError):
            if inspect.iscoroutinefunction(getattr(f, '__call__')):
                return _wrap_sync(f)
        return f

    raise ValueError('Can only synchronize coroutine callables (`async def`) or coroutines (values returned by `async def`), or pass through synchronous callables, but "%s" was given.' % f)
