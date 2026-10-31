"""
Test utilities for :py:mod:`betty.console`.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, final, override

from betty import console
from betty.console import Command, CommandDefinition, CommandFunction, ExitCode
from betty.uis.no_op import NoOpUi

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.user.ui import Ui


@CommandDefinition("no-op", label="No-op")
class NoOpCommand(Command):
    """
    A command that does nothing.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> None:
        return None


def new_raising_command(exception: BaseException, /) -> CommandDefinition:
    """
    Create a new command that raises the given exception.
    """

    @CommandDefinition("raising", label="Raising")
    class _RaisingCommand(Command):
        @override
        async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
            return self._invoke

        async def _invoke(self) -> None:
            raise exception

    return _RaisingCommand.definition


@final
@dataclass
class Result:
    """
    A console run result.
    """

    exit_code: int
    stderr: str
    stdout: str


async def run(
    command: console.Command | None,
    *args: str,
    expected_exit_code: ExitCode = ExitCode.OK,
    ui: Ui | None = None,
) -> Result:
    """
    Run a Betty console command.
    """
    stderr_f = StringIO()
    stdout_f = StringIO()
    with redirect_stderr(stderr_f), redirect_stdout(stdout_f):
        try:
            await console.run([command] if command else (), args, ui=ui or NoOpUi())
        except SystemExit as exception:
            if exception.code is None:
                exit_code = 0  # pragma: no cover
            elif isinstance(exception.code, int):
                exit_code = exception.code
            else:
                exit_code = 1  # pragma: no cover
        except BaseException as error:  # pragma: no cover
            raise AssertionError(f"The console did not raise {SystemExit}") from error
        else:  # pragma: no cover
            raise AssertionError(f"The console did not raise {SystemExit}")

    stderr_f.seek(0)
    stderr = stderr_f.read()
    stdout_f.seek(0)
    stdout = stdout_f.read()

    assert exit_code == expected_exit_code, f"""
The Betty command `{" ".join(args)}` unexpectedly exited with code {exit_code}, but {expected_exit_code} was expected.
Stdout:
{stdout}
Stderr:
{stderr}
"""
    return Result(exit_code, stderr, stdout)
