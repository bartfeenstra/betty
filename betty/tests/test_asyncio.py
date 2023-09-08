from typing import Any

import pytest

from betty.asyncio import sync, wait


class TestWait:
    async def test(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        async def _async() -> str:
            return expected
        actual = wait(_async())
        assert expected == actual

    def test_nested_sync_and_async(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        async def _async_one() -> str:
            return _sync()

        def _sync() -> str:
            return wait(_async_two())

        async def _async_two() -> str:
            return expected

        assert expected == wait(_async_one())

    # @todo See https://docs.python.org/3/library/asyncio-runner.html#asyncio.run
    # @todo Do we need to test with SIGINT as well?
    # @todo
    # @todo
    @pytest.mark.parametrize('exception', [
        KeyboardInterrupt,
        RuntimeError,
    ])
    def test_with_exception(self, exception: type[Exception]) -> None:
        async def _async() -> str:
            raise exception
        with pytest.raises(exception):
            wait(_async())


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

    @pytest.mark.parametrize('exception', [
        KeyboardInterrupt,
        RuntimeError,
    ])
    def test_with_exception(self, exception: type[Exception]) -> None:
        @sync
        async def _async() -> str:
            raise exception
        with pytest.raises(exception):
            _async()
