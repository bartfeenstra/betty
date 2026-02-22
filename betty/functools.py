"""
Provide functional programming utilities.
"""

from __future__ import annotations

import contextlib
from asyncio import sleep
from itertools import chain
from time import time
from typing import TYPE_CHECKING, Any, final

from betty.asyncio import resolve_await
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Iterator


def map_suppress[T, U](
    raising_map: Callable[[T], U],
    exception_type: type[BaseException],
    items: Iterable[T],
    /,
) -> Iterator[U]:
    """
    Map values, skipping those for which the application of `raising_map` raises errors.
    """
    for item in items:
        try:
            yield raising_map(item)
        except exception_type:
            continue


class Do[**DoFP, DoFReturnT]:
    """
    A functional implementation of do-while functionality, with retries and timeouts.
    """

    def __init__(
        self,
        do: Callable[DoFP, DoFReturnT | Awaitable[DoFReturnT]],
        *do_args: DoFP.args,
        **do_kwargs: DoFP.kwargs,
    ):
        self._do = do
        self._do_args = do_args
        self._do_kwargs = do_kwargs

    async def until(
        self,
        *conditions: Callable[[DoFReturnT], None | bool | Awaitable[None | bool]],
        retries: int = 5,
        timeout: int = 300,
        interval: int | float = 0.1,
    ) -> DoFReturnT:
        """
        Perform the 'do' until it succeeds or as long as the given arguments allow.

        :param timeout: The timeout in seconds.
        :param interval: The interval between 'loops' in seconds.
        """
        start_time = time()
        while True:
            retries -= 1
            try:
                do_result = await resolve_await(
                    self._do(*self._do_args, **self._do_kwargs)
                )
                for condition in conditions:
                    if await resolve_await(condition(do_result)) is False:
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


def unique[ValueT](
    *values: Iterable[ValueT], key: Callable[[ValueT], Any] | None = None
) -> Iterator[ValueT]:
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


def passthrough[T](value: T, /) -> T:
    """
    Return the value.
    """
    return value


def suppress[**P, T](
    target: Callable[P, T], *exceptions: type[BaseException]
) -> Callable[P, T | Void]:
    """
    Return the value, but suppress any errors.
    """

    def _suppress(*target_args: P.args, **target_kwargs: P.kwargs) -> T | Void:
        with contextlib.suppress(*exceptions):
            return target(*target_args, **target_kwargs)
        return Void

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
class Result[**P, T]:
    """
    Decorate a callable and store its return value or raised exception.
    """

    __slots__ = "_error", "_result", "_target"
    _error: BaseException
    _result: T

    def __init__(self, target: Callable[P, T], /):
        self._target = target

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Call the target.
        """
        try:
            self._result = self._target(*args, **kwargs)
            return self._result
        except BaseException as error:
            self._error = error
            raise

    def result(self) -> T:
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
