import logging
from unittest.mock import Mock

import pytest

from betty.user import Severity, UserTimeoutError
from betty.user.no_op import NoOpUser


class TestNoOpUser:
    async def test_exception(self) -> None:
        sut = NoOpUser()
        await sut.exception()

    async def test_message(self) -> None:
        sut = NoOpUser()
        await sut.message("Hello, world!", Severity.DEBUG)

    async def test_log(self) -> None:
        sut = NoOpUser()
        await sut.log(Mock(logging.LogRecord))

    async def test_progress(self) -> None:
        sut = NoOpUser()
        async with sut.progress("Hello, world!"):
            pass

    async def test_ask_confirmation(self) -> None:
        sut = NoOpUser()
        with pytest.raises(UserTimeoutError):
            await sut.ask_confirmation("Hello, world!")

    async def test_ask_input(self) -> None:
        sut = NoOpUser()
        with pytest.raises(UserTimeoutError):
            await sut.ask_input("Hello, world!")
