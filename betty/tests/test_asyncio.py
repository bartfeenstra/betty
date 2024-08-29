from betty.asyncio import wait_to_thread, make_async


class TestWaitToThread:
    async def test(self) -> None:
        expected = "Hello, oh asynchronous, world!"

        async def _async() -> str:
            return expected

        actual = wait_to_thread(_async())
        assert actual == expected


class TestMakeAsync:
    async def test(self) -> None:
        sentinel = object()

        def sync() -> object:
            return sentinel

        assert await make_async(sync)() is sentinel
