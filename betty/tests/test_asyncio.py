import asyncio
import multiprocessing
import os
import signal
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from pytest_mock import MockerFixture

from betty.asyncio import sync, wait


class TestWait:
    async def test(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        async def _async() -> str:
            return expected
        actual = wait(_async())
        assert expected == actual


@asynccontextmanager
async def _test_interrupt_set_exit_sentinel(start_sentinel: threading.Event, exit_sentinel: threading.Event) -> AsyncIterator[None]:
    try:
        start_sentinel.set()
        yield
    finally:
        exit_sentinel.set()


@sync
async def _test_interrupt_target(start_sentinel: threading.Event, exit_sentinel: threading.Event) -> None:
    async with _test_interrupt_set_exit_sentinel(start_sentinel, exit_sentinel):
        for _ in range(0, 999):
            await asyncio.sleep(1)


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

    def test_interrupt(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        start_sentinel = multiprocessing.Manager().Event()
        exit_sentinel = multiprocessing.Manager().Event()
        process = multiprocessing.Process(
            target=_test_interrupt_target,
            args=(start_sentinel, exit_sentinel),
        )
        process.start()
        start_sentinel.wait()
        os.kill(
            process.pid,  # type: ignore[arg-type]
            signal.SIGINT,
        )
        process.join()
        assert process.exitcode is not None
        assert process.exitcode > 0
        assert exit_sentinel.is_set()
