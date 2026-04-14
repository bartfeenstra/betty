"""
Provide functional programming utilities.
"""

from __future__ import annotations

import contextlib
import threading
from asyncio import sleep
from itertools import chain
from time import time
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    Self,
    final,
    overload,
    runtime_checkable,
)

from betty.asyncio import resolve_await
from betty.typing import Void, threadsafe

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
        interval: float = 0.1,
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
                        raise RuntimeError(  # noqa: TRY301
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
) -> Callable[P, T | type[Void]]:
    """
    Return the value, but suppress any errors.
    """

    def _suppress(*target_args: P.args, **target_kwargs: P.kwargs) -> T | type[Void]:
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
        except BaseException as error:
            self._error = error
            raise
        else:
            return self._result

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


type DecoratorCallableType[
    **DecoratorP,
    DecoratorReturnT,
    **DecoratedP,
    DecoratedReturnT,
] = Callable[
    [Callable[DecoratedP, DecoratedReturnT]], Callable[DecoratorP, DecoratorReturnT]
]


@runtime_checkable
class _DecoratedDescriptorCallableType[**P, ReturnT](Protocol):
    def __get__[T](
        self, instance: T | None, owner: type[T] | None = None, /
    ) -> Callable[P, ReturnT]:
        pass  # pragma: nocover


type DecoratedCallableType[**P, ReturnT] = (
    _DecoratedDescriptorCallableType[P, ReturnT] | Callable[P, ReturnT]
)


@final
class DecoratedCallable[**P, ReturnT]:
    """
    Apply a decorator to a callable.
    """

    __slots__ = "_decorated", "_decorator"

    def __init__[**DecoratedP, DecoratedReturnT](
        self,
        decorator: DecoratorCallableType[P, ReturnT, DecoratedP, DecoratedReturnT],
        decorated: DecoratedCallableType[DecoratedP, DecoratedReturnT],
        /,
    ):
        self._decorator = decorator
        self._decorated = decorated

    def __get__[T](
        self, instance: T | None, owner: type[T] | None = None
    ) -> Callable[P, ReturnT]:
        if isinstance(self._decorated, _DecoratedDescriptorCallableType):
            decorated = self._decorated.__get__(instance, owner)
        else:
            decorated = self._decorated
        return self._decorator(
            decorated,  # ty:ignore[invalid-argument-type]
        )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ReturnT:
        """
        Call the decorated function.
        """
        if not callable(self._decorated):
            raise TypeError(f"{self._decorated} is not supported")
        return self._decorator(
            self._decorated,  # ty:ignore[invalid-argument-type]
        )(*args, **kwargs)


class CallableDecorator[**P, ReturnT, **DecoratedP, DecoratedReturnT]:
    """
    An object capable of decorating a callable.
    """

    def __init__(
        self,
        *,
        callable_decorator: DecoratorCallableType[
            P, ReturnT, DecoratedP, DecoratedReturnT
        ],
    ):
        self.__callable_decorator = callable_decorator

    @overload
    def __call__(self) -> Self:
        pass

    @overload
    def __call__(
        self, decorated: DecoratedCallableType[DecoratedP, DecoratedReturnT]
    ) -> DecoratedCallable[P, ReturnT]:
        pass

    def __call__(self, decorated=None):
        """
        Decorate a callable.
        """
        if decorated is None:
            return self
        return DecoratedCallable(self.__callable_decorator, decorated)


@final
@threadsafe
class LazyReCallable[ValueT]:
    """
    A value that can be called multiple times while always returning the exact same value.

    The proxied callable will at most be called once.
    """

    __slots__ = "_factory", "_lock", "_value"
    _value: ValueT

    def __init__(self, factory: Callable[[], ValueT], /):
        self._factory = factory
        self._lock = threading.Lock()

    def __call__(self) -> ValueT:
        """
        Get the value.
        """
        # Check if the value was created already so we avoid acquiring the lock.
        if not hasattr(self, "_value"):
            with self._lock:
                # Check if the value was created since we last checked (this is usually done within the lock anyway).
                if not hasattr(self, "_value"):
                    self._value = self._factory()
        return self._value
