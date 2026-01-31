from betty.asyncio import resolve_await


async def test_resolve_await__with_awaitable() -> None:
    value = object()

    def _awaitable() -> object:
        return value

    assert await resolve_await(_awaitable()) is value


async def test_resolve_await__without_awaitable() -> None:
    value = object()
    assert await resolve_await(value) is value
