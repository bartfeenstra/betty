import logging
from contextlib import redirect_stdout
from io import StringIO

import pytest

from betty.assertion import assert_int
from betty.console.user import ConsoleUser
from betty.locale.localizable import Plain
from betty.user import Verbosity


class TestConsoleUser:
    async def test_connect__and_disconnect(self) -> None:
        sut = ConsoleUser()
        await sut.connect()
        await sut.disconnect()

    async def test___aenter____and___aexit__(self) -> None:
        async with ConsoleUser():
            pass

    async def test_verbosity__before_connect(self) -> None:
        sut = ConsoleUser()
        sut.verbosity = Verbosity.MORE_VERBOSE
        async with sut:
            assert sut.verbosity is Verbosity.MORE_VERBOSE

    async def test_verbosity__after_connect(self) -> None:
        async with ConsoleUser() as sut:
            sut.verbosity = Verbosity.MORE_VERBOSE
            assert sut.verbosity is Verbosity.MORE_VERBOSE

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (False, Verbosity.DEFAULT),
            (True, Verbosity.VERBOSE),
            (True, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_exception(
        self, expected: bool, verbosity: Verbosity
    ) -> None:
        class _Exception(Exception):
            pass

        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                try:
                    raise _Exception(message)
                except _Exception:
                    await sut.message_exception()
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        assert _Exception.__name__ in stdout_str
        assert __file__ in stdout_str
        assert message in stdout_str
        if expected:
            assert "locals" in stdout_str

    async def test_message_error(self) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                await sut.message_error(Plain(message))
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        assert message in stdout_str

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (True, Verbosity.DEFAULT),
            (True, Verbosity.VERBOSE),
            (True, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_warning(self, expected: bool, verbosity: Verbosity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                await sut.message_warning(Plain(message))
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (True, Verbosity.DEFAULT),
            (True, Verbosity.VERBOSE),
            (True, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_information(
        self, expected: bool, verbosity: Verbosity
    ) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                await sut.message_information(Plain(message))
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (False, Verbosity.DEFAULT),
            (True, Verbosity.VERBOSE),
            (True, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_information_details(
        self, expected: bool, verbosity: Verbosity
    ) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                await sut.message_information_details(Plain(message))
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (False, Verbosity.DEFAULT),
            (False, Verbosity.VERBOSE),
            (True, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_debug(self, expected: bool, verbosity: Verbosity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                await sut.message_debug(Plain(message))
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (False, Verbosity.DEFAULT),
            (False, Verbosity.VERBOSE),
            (False, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_log(self, expected: bool, verbosity: Verbosity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                await sut.message_log(
                    logging.LogRecord(
                        "name", logging.NOTSET, __file__, 0, message, (), None
                    )
                )
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (False, Verbosity.QUIET),
            (True, Verbosity.DEFAULT),
            (True, Verbosity.VERBOSE),
            (True, Verbosity.MORE_VERBOSE),
            (True, Verbosity.MOST_VERBOSE),
        ],
    )
    async def test_message_progress(self, expected: bool, verbosity: Verbosity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with ConsoleUser() as sut:
                sut.verbosity = verbosity
                async with sut.message_progress(Plain(message)) as progress:
                    await progress.add(2)
                    await progress.done(2)
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "stdin"),
        [
            (True, "y"),
            (False, "n"),
            (True, "x\ny"),
        ],
    )
    async def test_ask_confirmation(self, expected: bool, stdin: str) -> None:
        stdin = StringIO(stdin)
        async with ConsoleUser() as sut:
            assert await sut.ask_confirmation(Plain(""), stdin=stdin) is expected

    @pytest.mark.parametrize(
        "confirmation",
        [True, False],
    )
    async def test_ask_confirmation__with_default(self, confirmation: bool) -> None:
        stdin = StringIO("")
        async with ConsoleUser() as sut:
            assert (
                await sut.ask_confirmation(Plain(""), stdin=stdin, default=confirmation)
                is confirmation
            )

    async def test_ask_input__minimal(self) -> None:
        value = "Hello, world!"
        stdin = StringIO(f"{value}")
        async with ConsoleUser() as sut:
            assert await sut.ask_input(Plain(""), stdin=stdin) == value

    async def test_ask_input__with_assertion(self) -> None:
        def _assertion(value: str) -> int:
            return assert_int()(int(value))

        stdin = StringIO("123")
        async with ConsoleUser() as sut:
            assert (
                await sut.ask_input(Plain(""), stdin=stdin, assertion=_assertion) == 123
            )

    async def test_ask_input__with_default(self) -> None:
        default = "Hello, world!"
        stdin = StringIO("")
        async with ConsoleUser() as sut:
            assert (
                await sut.ask_input(Plain(""), stdin=stdin, default=default) == default
            )

    async def test_ask_input__with_assertion_and_default(self) -> None:
        def _assertion(value: str) -> int:
            return assert_int()(int(value))

        stdin = StringIO("")
        async with ConsoleUser() as sut:
            assert (
                await sut.ask_input(
                    Plain(""), stdin=stdin, assertion=_assertion, default="123"
                )
                == 123
            )
