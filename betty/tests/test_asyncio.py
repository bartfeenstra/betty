from betty.asyncio import ensure_await


async def test_ensure_await__with_awaitable() -> None:
    value = object()

    def _awaitable() -> object:
        return value

    assert await ensure_await(_awaitable()) is value


async def test_ensure_await__without_awaitable() -> None:
    value = object()
    assert await ensure_await(value) is value
