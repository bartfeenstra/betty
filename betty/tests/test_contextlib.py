from __future__ import annotations

from contextlib import suppress

from betty.contextlib import SynchronizedContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


class DummyAsynchronousContextManager:
    def __init__(self):
        self.entered = False
        self.exited = False
        self.exc_type: type[BaseException] | None = None
        self.exc_val: BaseException | None = None
        self.exc_tb: TracebackType | None = None

    async def __aenter__(self):
        self.entered = True

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb


class TestSynchronizedContextManager:
    async def test(self) -> None:
        asynchronous_context_manager = DummyAsynchronousContextManager()
        sut = SynchronizedContextManager(asynchronous_context_manager)
        with sut:
            pass
        assert asynchronous_context_manager.entered
        assert asynchronous_context_manager.exited

    async def test_with_error(self) -> None:
        asynchronous_context_manager = DummyAsynchronousContextManager()
        sut = SynchronizedContextManager(asynchronous_context_manager)
        error = RuntimeError()
        with suppress(RuntimeError), sut:
            raise error
        assert asynchronous_context_manager.entered
        assert asynchronous_context_manager.exited
        assert asynchronous_context_manager.exc_type is RuntimeError
        assert asynchronous_context_manager.exc_val is error
        assert asynchronous_context_manager.exc_tb is error.__traceback__
