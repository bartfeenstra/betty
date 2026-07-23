import logging
from contextlib import redirect_stdout
from io import StringIO

import pytest

from betty.assertions.int import assert_int
from betty.localizer import default_localizer
from betty.rich.user import RichUser
from betty.user import Severity


class TestRichUser:
    async def test_console(self) -> None:
        sut = RichUser()
        assert sut.console

    async def test_localizer(self) -> None:
        sut = RichUser()
        assert sut.localizer is default_localizer

    @pytest.mark.parametrize(
        ("expected", "severity"),
        [
            (False, Severity.ERROR),
            (False, Severity.WARN),
            (False, Severity.CONFIRM),
            (False, Severity.INFO),
            (False, Severity.DEBUG),
        ],
    )
    async def test_log_handler(self, expected: bool, severity: Severity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            RichUser(severity=severity)
            logging.getLogger().debug(message)
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "severity"),
        [
            (False, Severity.ERROR),
            (False, Severity.WARN),
            (False, Severity.CONFIRM),
            (False, Severity.INFO),
            (True, Severity.DEBUG),
        ],
    )
    async def test_exception(self, expected: bool, severity: Severity) -> None:
        class _Exception(Exception):
            pass

        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            sut = RichUser(severity=severity)
            try:
                raise _Exception(message)  # noqa: TRY301
            except _Exception:
                await sut.exception()
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        assert _Exception.__name__ in stdout_str
        assert __file__ in stdout_str
        assert message in stdout_str
        if expected:
            assert "locals" in stdout_str

    @pytest.mark.parametrize(
        ("expected", "severity"),
        [
            (False, Severity.ERROR),
            (False, Severity.WARN),
            (False, Severity.CONFIRM),
            (True, Severity.INFO),
            (True, Severity.DEBUG),
        ],
    )
    async def test_message(self, expected: bool, severity: Severity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            sut = RichUser(severity=severity)
            await sut.message(message, Severity.INFO)
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "severity"),
        [
            (False, Severity.ERROR),
            (False, Severity.WARN),
            (False, Severity.CONFIRM),
            (True, Severity.INFO),
            (True, Severity.DEBUG),
        ],
    )
    async def test_log(self, expected: bool, severity: Severity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            sut = RichUser(severity=severity)
            await sut.log(
                logging.LogRecord("name", logging.INFO, __file__, 0, message, (), None)
            )
        stdout.seek(0)
        stdout_str = stdout.read().replace("\n", "")
        if expected:
            assert message in stdout_str
        else:
            assert message not in stdout_str

    @pytest.mark.parametrize(
        ("expected", "severity"),
        [
            (False, Severity.ERROR),
            (False, Severity.WARN),
            (True, Severity.CONFIRM),
            (True, Severity.INFO),
            (True, Severity.DEBUG),
        ],
    )
    async def test_progress(self, expected: bool, severity: Severity) -> None:
        message = "Hello, world!"
        stdout = StringIO()
        with redirect_stdout(stdout):
            sut = RichUser(severity=severity)
            async with sut.progress(message) as progress:
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
        sut = RichUser()
        assert await sut.ask_confirmation("", stdin=stdin) is expected

    @pytest.mark.parametrize(
        "confirmation",
        [True, False],
    )
    async def test_ask_confirmation__with_default(self, confirmation: bool) -> None:
        stdin = StringIO("")
        sut = RichUser()
        assert (
            await sut.ask_confirmation("", stdin=stdin, default=confirmation)
            is confirmation
        )

    async def test_ask_input__minimal(self) -> None:
        value = "Hello, world!"
        stdin = StringIO(f"{value}")
        sut = RichUser()
        assert await sut.ask_input("", stdin=stdin) == value

    async def test_ask_input__with_assertion(self) -> None:
        def _assertion(value: str) -> int:
            return assert_int()(int(value))

        stdin = StringIO("123")
        sut = RichUser()
        assert await sut.ask_input("", stdin=stdin, assertion=_assertion) == 123

    async def test_ask_input__with_default(self) -> None:
        default = "Hello, world!"
        stdin = StringIO("")
        sut = RichUser()
        assert await sut.ask_input("", stdin=stdin, default=default) == default

    async def test_ask_input__with_assertion_and_default(self) -> None:
        def _assertion(value: str) -> int:
            return assert_int()(int(value))

        stdin = StringIO("")
        sut = RichUser()
        assert (
            await sut.ask_input("", stdin=stdin, assertion=_assertion, default="123")
            == 123
        )
