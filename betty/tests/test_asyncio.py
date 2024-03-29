from typing import Any

from betty.asyncio import sync, wait


class TestWait:
    async def test(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        async def _async() -> str:
            return expected
        actual = wait(_async())
        assert expected == actual


class TestSync:
    async def test_call_decorated_coroutinefunction_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        @sync
        async def _async() -> str:
            return expected
        actual = _async()
        assert expected == actual

    async def test_call_decorated_callable_coroutinemethod_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        class _Sync:
            @sync
            async def __call__(self, *args: Any, **kwargs: Any) -> str:
                return expected
        actual = _Sync()()
        assert expected == actual

    async def test_call_wrapped_coroutinecallable_object_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        class _Sync:
            async def __call__(self, *args: Any, **kwargs: Any) -> str:
                return expected
        actual = sync(_Sync())()
        assert expected == actual

    async def test_call_nested_sync_and_async(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        @sync
        async def _async_one() -> str:
            return _sync()

        def _sync() -> str:
            return _async_two()

        @sync
        async def _async_two() -> str:
            return expected

        assert expected == _async_one()
