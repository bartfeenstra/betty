from typing import Any

from betty.asyncio import LazyReAwaitable, resolve_await


async def test_resolve_await__with_awaitable() -> None:
    value = object()

    def _awaitable() -> object:
        return value

    assert await resolve_await(_awaitable()) is value


async def test_resolve_await__without_awaitable() -> None:
    value = object()
    assert await resolve_await(value) is value


class TestLazyReAwaitable:
    async def test___await__(self) -> None:
        value = object()

        async def _awaitable() -> Any:
            return value

        sut = LazyReAwaitable(_awaitable)
        assert await sut is value
        assert await sut is value
