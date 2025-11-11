"""
Provide functional programming utilities.
"""

from __future__ import annotations

import contextlib
from asyncio import sleep
from itertools import chain
from time import time
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    TypeVar,
    final,
)

from betty.asyncio import ensure_await
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Iterator

_T = TypeVar("_T")
_P = ParamSpec("_P")


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
                do_result = await ensure_await(
                    self._do(*self._do_args, **self._do_kwargs)
                )
                for condition in conditions:
                    if await ensure_await(condition(do_result)) is False:
                        raise RuntimeError(
                            f"Condition {condition} was not met for {do_result}."
                        )
            except Exception:
                if retries == 0:
                    raise
                if time() - start_time > timeout:
                    raise
                await sleep(interval)
            else:
                return do_result


_ValueT = TypeVar("_ValueT")
_KeyT = TypeVar("_KeyT")


def unique(
    *values: Iterable[_ValueT], key: Callable[[_ValueT], Any] | None = None
) -> Iterator[_ValueT]:
    """
    Yield the first occurrences of values in a sequence.

    For the purpose of filtering duplicate values from an iterable,
    this works similar to :py:class:`set`, except that this class
    supports non-hashable values. It is therefore slightly slower
    than :py:class:`set`.
    """
    seen_value_keys = []
    if key is None:
        key = passthrough
    for value in chain(*values):
        value_key = key(value)
        if value_key not in seen_value_keys:
            seen_value_keys.append(value_key)
            yield value


def passthrough(value: _T) -> _T:
    """
    Return the value.
    """
    return value


def suppress(
    target: Callable[_P, _T], *exceptions: type[BaseException]
) -> Callable[_P, _T | Void]:
    """
    Return the value, but suppress any errors.
    """

    def _suppress(*target_args: _P.args, **target_kwargs: _P.kwargs) -> _T | Void:
        with contextlib.suppress(*exceptions):
            return target(*target_args, **target_kwargs)
        return Void()

    return _suppress


class ResultUnavailable(RuntimeError):
    """
    A :py:attr:`betty.functools.Result.result` is unavailable.
    """

    def __init__(self):
        super().__init__(
            "The result is unavailable because the target has not been called yet."
        )


@final
class Result(Generic[_P, _T]):
    """
    Decorate a callable and store its return value or raised exception.
    """

    __slots__ = "_error", "_result", "_target"
    _error: BaseException
    _result: _T

    def __init__(self, target: Callable[_P, _T]):
        self._target = target

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        """
        Call the target.
        """
        try:
            self._result = self._target(*args, **kwargs)
            return self._result
        except BaseException as error:
            self._error = error
            raise

    def result(self) -> _T:
        """
        Get the target's return value.

        If the target raised an exception, calling this method will re-raise the exception.
        """
        try:
            raise self._error
        except AttributeError:
            try:
                return self._result
            except AttributeError:
                raise ResultUnavailable from None
