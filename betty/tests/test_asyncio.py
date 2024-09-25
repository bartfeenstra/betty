from betty.asyncio import wait_to_thread


class TestWaitToThread:
    async def test(self) -> None:
        expected = "Hello, oh asynchronous, world!"

        async def _async() -> str:
            return expected

        actual = wait_to_thread(_async)
        assert actual == expected
