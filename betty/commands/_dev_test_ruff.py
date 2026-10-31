from __future__ import annotations

from subprocess import CalledProcessError, check_call
from typing import TYPE_CHECKING, final, override

from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition("dev-test-ruff", label="Run Ruff tests")
class DevTestRuff(DevCommand):
    """
    .. plugin:: command:dev-test-ruff.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> CommandResult:
        with self._error_unexpected_recoverable(CalledProcessError):
            check_call(["python", "-m", "ruff", "check", "--preview", "."])
            check_call(["python", "-m", "ruff", "format", "--preview", "--check", "."])
