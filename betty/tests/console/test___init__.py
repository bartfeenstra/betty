import argparse
from asyncio import CancelledError
from collections.abc import Awaitable, Callable
from threading import Thread
from typing import Any

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.config.file import write_configuration_file
from betty.console import SystemExitCode, call_command_func, main_standalone
from betty.console.command import Command, CommandDefinition
from betty.exception import UserFacingException
from betty.functools import Result, suppress
from betty.locale.localizable import Plain
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.test_utils.console import run
from betty.user import Verbosity


@CommandDefinition(
    id="no-op",
    label=Plain("No-op"),
)
class _NoOpCommand(Command):
    @override
    async def configure(
        self, parser: argparse.ArgumentParser
    ) -> Callable[..., Awaitable[None]]:
        return self._invoke

    async def _invoke(self) -> None:
        pass


def _create_raising_command(exception: BaseException) -> CommandDefinition:
    class _RaisingCommand(Command):
        @override
        async def configure(
            self, parser: argparse.ArgumentParser
        ) -> Callable[..., Awaitable[None]]:
            return self._invoke

        async def _invoke(self) -> None:
            raise exception

    return CommandDefinition(
        id="raising",
        label=Plain("Raising"),
        cls=_RaisingCommand,
    )


async def test_main__without_arguments(new_temporary_app: App) -> None:
    await run(new_temporary_app, expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE)


async def test_main__help(new_temporary_app: App) -> None:
    await run(new_temporary_app, "--help")


async def test_main__version(new_temporary_app: App) -> None:
    result = await run(new_temporary_app, "--version")
    assert "Betty" in result.stdout


async def test_main__commands(new_temporary_app: App) -> None:
    await run(new_temporary_app, "--commands")


async def test_main__with_unknown_command(new_temporary_app: App) -> None:
    await run(
        new_temporary_app,
        "unknown-command",
        expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
    )


@pytest.mark.parametrize(
    ("expected", "command"),
    [
        (SystemExitCode.OK, _NoOpCommand.plugin),
        (
            SystemExitCode.ERROR_UNEXPECTED,
            _create_raising_command(UserFacingException(Plain(""))),
        ),
        (SystemExitCode.USER_QUIT, _create_raising_command(CancelledError())),
        (SystemExitCode.USER_QUIT, _create_raising_command(KeyboardInterrupt())),
        (SystemExitCode.ERROR_UNEXPECTED, _create_raising_command(RuntimeError())),
    ],
)
async def test_main__with_user_facing_exception(
    expected: SystemExitCode,
    command: CommandDefinition,
    mocker: MockerFixture,
    new_temporary_app: App,
) -> None:
    mocker.patch(
        "betty.console.command.COMMAND_REPOSITORY",
        new=StaticPluginRepository(CommandDefinition, command),
    )
    await run(
        new_temporary_app,
        command.id,
        expected_exit_code=expected,
    )


@pytest.mark.parametrize(
    ("expected", "command"),
    [
        (SystemExitCode.OK, _NoOpCommand.plugin),
        (
            SystemExitCode.ERROR_UNEXPECTED,
            _create_raising_command(UserFacingException(Plain(""))),
        ),
        (SystemExitCode.USER_QUIT, _create_raising_command(CancelledError())),
        (SystemExitCode.USER_QUIT, _create_raising_command(KeyboardInterrupt())),
        (SystemExitCode.ERROR_UNEXPECTED, _create_raising_command(RuntimeError())),
    ],
)
def test_main_standalone(
    expected: SystemExitCode, command: CommandDefinition, mocker: MockerFixture
) -> None:
    def _target() -> None:
        mocker.patch(
            "betty.console.command.COMMAND_REPOSITORY",
            new=StaticPluginRepository(CommandDefinition, command),
        )
        (mocker.patch("sys.argv", new=["betty", command.id]),)
        main_standalone()

    # Run this in a thread so as not to conflict with pytest-playwright-asyncio's session-scoped event loop.
    result = Result(_target)
    thread = Thread(target=suppress(result, BaseException))
    thread.start()
    thread.join()

    with pytest.raises(SystemExit) as exc_info:
        result.result()
    assert exc_info.value.code is expected


class TestVerbosity:
    @pytest.mark.parametrize(
        ("expected", "verbosity"),
        [
            (Verbosity.QUIET, "-q"),
            (Verbosity.DEFAULT, None),
            (Verbosity.VERBOSE, "-v"),
            (Verbosity.MORE_VERBOSE, "-vv"),
        ],
    )
    async def test(
        self,
        expected: Verbosity,
        mocker: MockerFixture,
        new_temporary_app: App,
        verbosity: str | None,
    ) -> None:
        mocker.patch(
            "betty.console.command.COMMAND_REPOSITORY",
            new=StaticPluginRepository(CommandDefinition, _NoOpCommand.plugin),
        )
        async with Project.new_temporary(new_temporary_app) as project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            args = ["no-op"]
            if verbosity is not None:
                args.append(verbosity)
            await run(new_temporary_app, *args)
            assert new_temporary_app.user.verbosity is expected


async def test_call_command_func() -> None:
    expected = {
        "foo": 123,
        "bar": False,
    }
    namespace = argparse.Namespace(**expected, _internal=None)

    async def _command_func(**kwargs: Any) -> None:
        assert kwargs == expected

    await call_command_func(_command_func, namespace)
