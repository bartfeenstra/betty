import logging
from unittest.mock import Mock

import pytest

from betty.locale.localizable import Plain
from betty.user import UserTimeoutError, Verbosity
from betty.user.no_op import NoOpUser


class TestNoOpUser:
    def test_verbosity(self) -> None:
        sut = NoOpUser()
        sut.verbosity  # noqa B018

    @pytest.mark.parametrize(
        "verbosity",
        [verbosity.value for verbosity in Verbosity],
    )
    async def test_set_verbosity(self, verbosity: Verbosity) -> None:
        sut = NoOpUser()
        await sut.set_verbosity(verbosity)

    async def test_connect__and_disconnect(self) -> None:
        sut = NoOpUser()
        await sut.connect()
        await sut.disconnect()

    async def test___aenter___and___aexit__(self) -> None:
        async with NoOpUser():
            pass

    async def test_message_exception(self) -> None:
        sut = NoOpUser()
        await sut.message_exception()

    async def test_message_error(self) -> None:
        sut = NoOpUser()
        await sut.message_error(Plain("Hello, world!"))

    async def test_message_warning(self) -> None:
        sut = NoOpUser()
        await sut.message_warning(Plain("Hello, world!"))

    async def test_message_information(self) -> None:
        sut = NoOpUser()
        await sut.message_information(Plain("Hello, world!"))

    async def test_message_information_details(self) -> None:
        sut = NoOpUser()
        await sut.message_information_details(Plain("Hello, world!"))

    async def test_message_debug(self) -> None:
        sut = NoOpUser()
        await sut.message_debug(Plain("Hello, world!"))

    async def test_message_log(self) -> None:
        sut = NoOpUser()
        await sut.message_log(Mock(logging.LogRecord))

    async def test_message_progress(self) -> None:
        sut = NoOpUser()
        async with sut.message_progress(Plain("Hello, world!")):
            pass

    async def test_ask_confirmation(self) -> None:
        sut = NoOpUser()
        with pytest.raises(UserTimeoutError):
            await sut.ask_confirmation(Plain("Hello, world!"))

    async def test_ask_input(self) -> None:
        sut = NoOpUser()
        with pytest.raises(UserTimeoutError):
            await sut.ask_input(Plain("Hello, world!"))
