"""
Provide asynchronous programming utilities.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, final, override

from betty.concurrent import ThreadSafeLock

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Generator


type ResolvableAwaitable[T] = Awaitable[T] | T


async def resolve_await[T](value: ResolvableAwaitable[T]) -> T:
    """
    Return a value, but await it first if it is awaitable.
    """
    if isawaitable(value):
        return await value  # ty:ignore[invalid-return-type]
    return value


class ReAwaitable[ValueT](metaclass=ABCMeta):
    """
    A value that can be awaited multiple times.
    """

    __slots__ = ()

    @abstractmethod
    def __await__(self) -> Generator[Any, Any, ValueT]:
        pass


@final
class LazyReAwaitable[ValueT](ReAwaitable[ValueT]):
    """
    A value that can be awaited multiple times while always returning the exact same value.

    The proxied awaitable will at most be awaited once.
    """

    __slots__ = "_factory", "_lock", "_value"
    _value: ValueT

    def __init__(self, factory: Callable[[], Awaitable[ValueT]], /):
        self._factory = factory
        self._lock = ThreadSafeLock()

    @override
    def __await__(self) -> Generator[Any, Any, ValueT]:
        # Check if the value was created already so we avoid acquiring the lock.
        if not hasattr(self, "_value"):
            yield from self._lock.acquire().__await__()
            try:
                # Check if the value was created since we last checked (this is usually done within the lock anyway).
                if not hasattr(self, "_value"):
                    self._value = yield from self._factory().__await__()
            finally:
                yield from self._lock.release().__await__()
        return self._value
