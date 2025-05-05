import pytest

from betty.locale.localizable import plain
from betty.user import UserTimeoutError
from betty.user.no_op import NoOpUser


class TestNoOpUser:
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
        await sut.message_error(plain("Hello, world!"))

    async def test_message_warning(self) -> None:
        sut = NoOpUser()
        await sut.message_warning(plain("Hello, world!"))

    async def test_message_information(self) -> None:
        sut = NoOpUser()
        await sut.message_information(plain("Hello, world!"))

    async def test_message_debug(self) -> None:
        sut = NoOpUser()
        await sut.message_debug(plain("Hello, world!"))

    async def test_message_progress(self) -> None:
        sut = NoOpUser()
        async with sut.message_progress(plain("Hello, world!")):
            pass

    async def test_ask_confirmation(self) -> None:
        sut = NoOpUser()
        with pytest.raises(UserTimeoutError):
            await sut.ask_confirmation(plain("Hello, world!"))

    async def test_ask_input(self) -> None:
        sut = NoOpUser()
        with pytest.raises(UserTimeoutError):
            await sut.ask_input(plain("Hello, world!"))
