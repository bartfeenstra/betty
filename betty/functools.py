import asyncio
import functools as stdfunctools
from typing import Iterable


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


async def asynciter(items: Iterable):
    if hasattr(items, '__aiter__'):
        async for item in items:
            yield item
        return
    for item in items:
        yield item


def sync(f):
    return asyncio.get_event_loop().run_until_complete(f)


def synced(f):
    @stdfunctools.wraps(f)
    def _synced(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))
    return _synced
