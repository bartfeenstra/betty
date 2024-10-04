from betty.asyncio import wait_to_thread, ensure_await


class TestWaitToThread:
    async def test(self) -> None:
        expected = "Hello, oh asynchronous, world!"

        async def _async() -> str:
            return expected

        actual = wait_to_thread(_async())
        assert actual == expected


class TestEnsureAwait:
    async def test_with_awaitable(self) -> None:
        value = object()

        def _awaitable() -> object:
            return value

        assert await ensure_await(_awaitable()) is value

    async def test_without_awaitable(self) -> None:
        value = object()
        assert await ensure_await(value) is value
