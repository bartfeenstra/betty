from inspect import iscoroutine
from typing import Any

from betty.asyncio import (
    LazyReAwaitable,
    resolve_await,
    resolve_coroutine_function,
)


async def test_resolve_await__with_awaitable() -> None:
    value = object()

    def _awaitable() -> object:
        return value

    assert await resolve_await(_awaitable()) is value


async def test_resolve_await__without_awaitable() -> None:
    value = object()
    assert await resolve_await(value) is value


class _Value:
    pass


def _function(value: _Value, /) -> _Value:
    return value


async def _coroutine_function(value: _Value, /) -> _Value:
    return value


async def test_resolve_coroutine_function__with_function() -> None:
    value = _Value()
    assert await resolve_coroutine_function(_function)(value) is value


async def test_resolve_coroutine_function__with__coroutine_function() -> None:
    value = _Value()
    assert await resolve_coroutine_function(_coroutine_function)(value) is value


async def test_resolve_coroutine_function__with__lambda() -> None:
    value = _Value()
    assert await resolve_coroutine_function(lambda value: value)(value) is value


async def test_resolve_coroutine_function__with__lambda_returns_coroutine() -> None:
    value = _Value()
    actual = await resolve_coroutine_function(_coroutine_function)(value)
    assert iscoroutine(actual)
    assert await actual is value


class TestLazyReAwaitable:
    async def test___await__(self) -> None:
        value = object()

        async def _awaitable() -> Any:
            return value

        sut = LazyReAwaitable(_awaitable)
        assert await sut is value
        assert await sut is value
