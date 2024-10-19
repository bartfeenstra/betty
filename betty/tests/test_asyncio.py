from betty.asyncio import ensure_await


class TestEnsureAwait:
    async def test_with_awaitable(self) -> None:
        value = object()

        def _awaitable() -> object:
            return value

        assert await ensure_await(_awaitable()) is value

    async def test_without_awaitable(self) -> None:
        value = object()
        assert await ensure_await(value) is value
