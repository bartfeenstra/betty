from __future__ import annotations

from os import environ
from subprocess import CalledProcessError, check_call
from typing import TYPE_CHECKING, final, override

from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult
from betty.dirs import root_directory

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition("dev-test-pytest", label="Run pytest tests")
class DevTestPytest(DevCommand):
    """
    .. plugin:: command:dev-test-pytest.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        parser.add_argument("pytest_args", nargs="*")
        return self._command_function

    async def _command_function(self, *, pytest_args: list[str]) -> CommandResult:
        with self._error_unexpected_recoverable(CalledProcessError):
            check_call(["python", "-m", "coverage", "erase"])
            check_call(
                ["python", "-m", "coverage", "run", "--module", "pytest", *pytest_args],
                env={
                    **environ,
                    "COVERAGE_PROCESS_START": str(root_directory / ".coveragerc"),
                    "PYTHONPATH": str(root_directory / "site"),
                },
            )
            check_call(["python", "-m", "coverage", "combine"])
            check_call([
                "python",
                "-m",
                "coverage",
                "report",
                "--skip-covered",
                "--skip-empty",
            ])
