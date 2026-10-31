from argparse import Namespace
from asyncio import CancelledError
from typing import Any

import pytest

from betty.console import CommandDefinition, CommandExit, ExitCode, call_command_func
from betty.exception import HumanFacingException
from betty.test_utils.console import NoOpCommand, new_raising_command, run
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.uis.no_op import NoOpUi
from betty.user import Severity


class TestCommandExit:
    def test(self) -> None:
        assert str(CommandExit(None)) == "A command exited with code 0"


async def test_run__without_arguments() -> None:
    await run(None, expected_exit_code=ExitCode.ERROR_USAGE)


async def test_run__help() -> None:
    await run(None, "--help")


async def test_run__commands() -> None:
    await run(None, "--commands")


async def test_run__with_unknown_command() -> None:
    await run(None, "unknown-command", expected_exit_code=ExitCode.ERROR_USAGE)


@pytest.mark.parametrize(
    ("expected", "command"),
    [
        (ExitCode.OK, NoOpCommand.definition),
        (
            ExitCode.ERROR_UNEXPECTED_RECOVERABLE,
            new_raising_command(HumanFacingException(DUMMY_LOCALIZABLE)),
        ),
        (ExitCode.USER_QUIT, new_raising_command(CancelledError())),
        (ExitCode.USER_QUIT, new_raising_command(KeyboardInterrupt())),
        (ExitCode.ERROR_UNEXPECTED_UNRECOVERABLE, new_raising_command(RuntimeError())),
    ],
)
async def test_run__with_user_facing_exception(
    expected: ExitCode, command: CommandDefinition
) -> None:
    await run(command.cls(), command.id, expected_exit_code=expected)


class TestVerbosity:
    @pytest.mark.parametrize(
        ("expected", "severity"),
        [
            (Severity.ERROR, "-qq"),
            (Severity.WARN, "-q"),
            (Severity.CONFIRM, None),
            (Severity.INFO, "-v"),
            (Severity.DEBUG, "-vv"),
        ],
    )
    async def test(self, expected: Severity, severity: str | None) -> None:
        ui = NoOpUi()
        args = ["no-op"]
        if severity is not None:
            args.append(severity)
        await run(NoOpCommand(), *args, ui=ui)
        assert ui.severity is expected


async def test_call_command_func() -> None:
    expected = {
        "foo": 123,
        "bar": False,
    }
    namespace = Namespace(**expected, _internal=None)

    async def _command_func(**kwargs: Any) -> None:
        assert kwargs == expected

    assert await call_command_func(_command_func, namespace) is ExitCode.OK


class TestCommandDefinition:
    def test_aliases(self) -> None:
        alias = "hello-world"
        sut = CommandDefinition("-", label="-", aliases=[alias])
        assert list(sut.aliases) == [alias]
