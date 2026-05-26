import logging
from contextlib import redirect_stdout
from io import StringIO

import pytest

from betty.assertions.int import assert_int
from betty.rich.user import RichUser
from betty.user import Verbosity


class TestRichUser:
    async def test_console(self) -> None:
        sut = RichUser()
        sut.console  # noqa: B018

    async def test_verbosity(self) -> None:
        sut = RichUser()
        sut.verbosity  # noqa: B018

    @pytest.mark.parametrize(
        "verbosity",
        [verbosity.value for verbosity in Verbosity],
    )
    async def test_set_verbosity(self, verbosity: Verbosity) -> None:
        async with RichUser() as sut:
            await sut.set_verbosity(verbosity)
            assert sut.verbosity is verbosity

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
    async def test_log_handler(self, expected: bool, verbosity: Verbosity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                logging.getLogger().debug(message)
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
    async def test_message_exception(
        self, expected: bool, verbosity: Verbosity
    ) -> None:
        class _Exception(Exception):
            pass

        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                try:
                    raise _Exception(message)  # noqa: TRY301
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
            async with RichUser() as sut:
                await sut.message_error(message)
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
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                await sut.message_warning(message)
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
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                await sut.message_information(message)
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
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                await sut.message_information_details(message)
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
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                await sut.message_debug(message)
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
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
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
            async with RichUser() as sut:
                await sut.set_verbosity(verbosity)
                async with sut.message_progress(message) as progress:
                    await progress.add(2)
                    await progress.done(2)
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "stdin_input"),
        [
            (True, "y"),
            (False, "n"),
            (True, "x\ny"),
        ],
    )
    async def test_ask_confirmation(self, expected: bool, stdin_input: str) -> None:
        stdin = StringIO(stdin_input)
        async with RichUser() as sut:
            assert await sut.ask_confirmation("", stdin=stdin) is expected

    @pytest.mark.parametrize(
        "confirmation",
        [True, False],
    )
    async def test_ask_confirmation__with_default(self, confirmation: bool) -> None:
        stdin = StringIO("")
        async with RichUser() as sut:
            assert (
                await sut.ask_confirmation("", stdin=stdin, default=confirmation)
                is confirmation
            )

    async def test_ask_input__minimal(self) -> None:
        value = "Hello, world!"
        stdin = StringIO(f"{value}")
        async with RichUser() as sut:
            assert await sut.ask_input("", stdin=stdin) == value

    async def test_ask_input__with_assertion(self) -> None:
        def _assertion(value: str) -> int:
            return assert_int()(int(value))

        stdin = StringIO("123")
        async with RichUser() as sut:
            assert await sut.ask_input("", stdin=stdin, assertion=_assertion) == 123

    async def test_ask_input__with_default(self) -> None:
        default = "Hello, world!"
        stdin = StringIO("")
        async with RichUser() as sut:
            assert await sut.ask_input("", stdin=stdin, default=default) == default

    async def test_ask_input__with_assertion_and_default(self) -> None:
        def _assertion(value: str) -> int:
            return assert_int()(int(value))

        stdin = StringIO("")
        async with RichUser() as sut:
            assert (
                await sut.ask_input(
                    "", stdin=stdin, assertion=_assertion, default="123"
                )
                == 123
            )
