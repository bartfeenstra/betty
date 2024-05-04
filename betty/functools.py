"""
Provide functional programming utilities.
"""

from __future__ import annotations

from asyncio import sleep
from inspect import isawaitable
from time import time
from typing import (
    Any,
    Iterable,
    Sized,
    TypeVar,
    Callable,
    Iterator,
    Generic,
    cast,
    ParamSpec,
    Awaitable,
)

T = TypeVar("T")
U = TypeVar("U")


def walk(item: Any, attribute_name: str) -> Iterable[Any]:
    """
    Walk over a graph of objects by following a single attribute.
    """
    child = getattr(item, attribute_name)

    # If the child has the requested attribute, yield it,
    if hasattr(child, attribute_name):
        yield child
        yield from walk(child, attribute_name)

    # Otherwise loop over the children and yield their attributes.
    try:
        child_children = iter(child)
    except TypeError:
        return
    for child_child in child_children:
        yield child_child
        yield from walk(child_child, attribute_name)


def slice_to_range(indices: slice, iterable: Sized) -> Iterable[int]:
    """
    Apply a slice to an iterable, and return the corresponding range.
    """
    length = len(iterable)

    if indices.start is None:
        start = 0
    else:
        # Ensure the stop index is within range.
        start = max(-length, min(length, indices.start))

    if indices.stop is None:
        stop = max(0, length)
    else:
        # Ensure the stop index is within range.
        stop = max(-length, min(length, indices.stop))

    if indices.step is None:
        step = 1
    else:
        step = indices.step

    return range(start, stop, step)


class _Result(Generic[T]):
    def __init__(self, value: T | None, _error: BaseException | None = None):
        assert not _error or value is None
        self._value = value
        self._error = _error

    @property
    def value(self) -> T:
        if self._error:
            raise self._error
        return cast(T, self._value)

    def map(self, f: Callable[[T], U]) -> _Result[U]:
        if self._error:
            return cast(_Result[U], self)
        try:
            return _Result(f(self.value))
        except Exception as e:
            return _Result(None, e)


def filter_suppress(
    raising_filter: Callable[[T], Any],
    exception_type: type[BaseException],
    items: Iterable[T],
) -> Iterator[T]:
    """
    Filter values, skipping those for which the application of `raising_filter` raises errors.
    """
    for item in items:
        try:
            raising_filter(item)
            yield item
        except exception_type:
            continue


_DoFReturnT = TypeVar("_DoFReturnT")
_DoFP = ParamSpec("_DoFP")


class Do(Generic[_DoFP, _DoFReturnT]):
    def __init__(
        self,
        f: Callable[_DoFP, _DoFReturnT | Awaitable[_DoFReturnT]],
        *args: _DoFP.args,
        **kwargs: _DoFP.kwargs,
    ):
        self._f = f
        self._args = args
        self._kwargs = kwargs

    async def until(
        self,
        *conditions: Callable[[_DoFReturnT], None | bool | Awaitable[None | bool]],
        retries: int = 5,
        timeout: int = 300,
        interval: int | float = 0.1,
    ) -> _DoFReturnT:
        start_time = time()
        while True:
            retries -= 1
            try:
                f_result_or_coroutine = self._f(*self._args, **self._kwargs)
                if isawaitable(f_result_or_coroutine):
                    f_result = await f_result_or_coroutine
                else:
                    f_result = f_result_or_coroutine
                for condition in conditions:
                    condition_result_or_coroutine = condition(f_result)
                    if isawaitable(condition_result_or_coroutine):
                        condition_result = await condition_result_or_coroutine
                    else:
                        condition_result = cast(
                            None | bool, condition_result_or_coroutine
                        )
                    if condition_result is False:
                        raise RuntimeError(
                            f"Condition {condition} was not met for {f_result}."
                        )
            except BaseException:
                if retries == 0:
                    raise
                if time() - start_time > timeout:
                    raise
                await sleep(interval)
            else:
                return f_result
