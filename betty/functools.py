"""
Provide functional programming utilities.
"""

from __future__ import annotations

from asyncio import sleep
from inspect import isawaitable
from itertools import chain
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
    TYPE_CHECKING,
)

from betty.warnings import deprecated

if TYPE_CHECKING:
    from collections.abc import MutableSequence

T = TypeVar("T")
U = TypeVar("U")


@deprecated(
    "This function is deprecated as of Betty 0.3.5, and will be removed in Betty 0.4.x. Instead, use a custom function, tailored to your data type."
)
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

    if indices.start is None:  # noqa SIM108
        start = 0
    else:
        # Ensure the stop index is within range.
        start = max(-length, min(length, indices.start))

    if indices.stop is None:
        stop = max(0, length)
    else:
        # Ensure the stop index is within range.
        stop = max(-length, min(length, indices.stop))

    step = 1 if indices.step is None else indices.step

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
    """
    A functional implementation of do-while functionality, with retries and timeouts.
    """

    def __init__(
        self,
        do: Callable[_DoFP, _DoFReturnT | Awaitable[_DoFReturnT]],
        *do_args: _DoFP.args,
        **do_kwargs: _DoFP.kwargs,
    ):
        self._do = do
        self._do_args = do_args
        self._do_kwargs = do_kwargs

    async def until(
        self,
        *conditions: Callable[[_DoFReturnT], None | bool | Awaitable[None | bool]],
        retries: int = 5,
        timeout: int = 300,
        interval: int | float = 0.1,
    ) -> _DoFReturnT:
        """
        Perform the 'do' until it succeeds or as long as the given arguments allow.

        :param timeout: The timeout in seconds.
        :param interval: The interval between 'loops' in seconds.
        """
        start_time = time()
        while True:
            retries -= 1
            try:
                do_result_or_coroutine = self._do(*self._do_args, **self._do_kwargs)
                if isawaitable(do_result_or_coroutine):
                    do_result = await do_result_or_coroutine
                else:
                    do_result = do_result_or_coroutine
                for condition in conditions:
                    condition_result_or_coroutine = condition(do_result)
                    if isawaitable(condition_result_or_coroutine):
                        condition_result = await condition_result_or_coroutine
                    else:
                        condition_result = cast(
                            None | bool, condition_result_or_coroutine
                        )
                    if condition_result is False:
                        raise RuntimeError(
                            f"Condition {condition} was not met for {do_result}."
                        )
            except BaseException:
                if retries == 0:
                    raise
                if time() - start_time > timeout:
                    raise
                await sleep(interval)
            else:
                return do_result


class Uniquifier(Generic[T]):
    """
    Yield the first occurrences of values in a sequence.

    For the purpose of filtering duplicate values from an iterable,
    this works similar to :py:class:`set`, except that this class
    supports non-hashable values. It is therefore slightly slower
    than :py:class:`set`.
    """

    def __init__(self, *values: Iterable[T]):
        self._values = chain(*values)
        self._seen: MutableSequence[T] = []

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        value = next(self._values)
        if value in self._seen:
            return next(self)
        self._seen.append(value)
        return value
