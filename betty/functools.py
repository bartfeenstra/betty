import asyncio
from functools import wraps
from inspect import iscoroutine, iscoroutinefunction
from typing import Iterable, AsyncIterable, Union


def walk(item, attribute_name):
    children = getattr(item, attribute_name)

    # If the child has the requested attribute, yield it,
    if hasattr(children, attribute_name):
        yield children
        yield from walk(children, attribute_name)

    # Otherwise loop over the children and yield their attributes.
    try:
        children = iter(children)
    except TypeError:
        return
    for child in children:
        yield child
        yield from walk(child, attribute_name)


async def asynciter(items: Union[Iterable, AsyncIterable]) -> AsyncIterable:
    if hasattr(items, '__aiter__'):
        async for item in items:
            yield item
        return
    for item in items:
        yield item


def sync(f):
    if iscoroutine(f):
        return asyncio.get_event_loop().run_until_complete(f)
    elif iscoroutinefunction(f):
        @wraps(f)
        def _synced(*args, **kwargs):
            return sync(f(*args, **kwargs))
        return _synced
    raise ValueError('Can only synchronize coroutine functions (`async def`) or coroutines (values returned by `async def`), but "%s" was given.' % f)
