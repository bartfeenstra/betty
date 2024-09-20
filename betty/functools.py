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
    TypeVar,
    Callable,
    Iterator,
    Generic,
    ParamSpec,
    Awaitable,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from collections.abc import MutableSequence

_T = TypeVar("_T")


def filter_suppress(
    raising_filter: Callable[[_T], Any],
    exception_type: type[BaseException],
    items: Iterable[_T],
) -> Iterator[_T]:
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
                        condition_result = condition_result_or_coroutine
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


_ValueT = TypeVar("_ValueT")
_KeyT = TypeVar("_KeyT")


class Uniquifier(Generic[_ValueT]):
    """
    Yield the first occurrences of values in a sequence.

    For the purpose of filtering duplicate values from an iterable,
    this works similar to :py:class:`set`, except that this class
    supports non-hashable values. It is therefore slightly slower
    than :py:class:`set`.
    """

    def __init__(
        self,
        *values: Iterable[_ValueT],
        key: Callable[[_ValueT], Any] | None = None,
    ):
        self._values = chain(*values)
        self._key = key or self._passthrough
        self._seen: MutableSequence[Any] = []

    @staticmethod
    def _passthrough(value: _ValueT) -> Any:
        return value

    def __iter__(self) -> Iterator[_ValueT]:
        return self

    def __next__(self) -> _ValueT:
        value = next(self._values)
        key = self._key(value)
        if key in self._seen:
            return next(self)
        self._seen.append(key)
        return value
