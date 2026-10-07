import logging
from unittest.mock import Mock

import pytest

from betty.uis.no_op import NoOpUi
from betty.user import Severity
from betty.user.error import UserFacingError
from betty.user.ui import UiTimeoutError


class TestNoOpUi:
    async def test_exception(self) -> None:
        sut = NoOpUi()
        await sut.exception()

    async def test_error(self) -> None:
        sut = NoOpUi()
        await sut.error(UserFacingError(""))

    async def test_message(self) -> None:
        sut = NoOpUi()
        await sut.message("Hello, world!", Severity.DEBUG)

    async def test_log(self) -> None:
        sut = NoOpUi()
        await sut.log(Mock(logging.LogRecord))

    async def test_progress(self) -> None:
        sut = NoOpUi()
        async with sut.progress("Hello, world!"):
            pass

    async def test_ask_confirmation(self) -> None:
        sut = NoOpUi()
        with pytest.raises(UiTimeoutError):
            await sut.ask_confirmation("Hello, world!")

    async def test_ask_input(self) -> None:
        sut = NoOpUi()
        with pytest.raises(UiTimeoutError):
            await sut.ask_input("Hello, world!")
