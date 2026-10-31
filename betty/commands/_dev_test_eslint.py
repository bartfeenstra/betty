from __future__ import annotations

import sys
from subprocess import CalledProcessError, check_call
from typing import TYPE_CHECKING, final, override

from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition("dev-test-eslint", label="Run ESLint tests")
class DevTestEslint(DevCommand):
    """
    .. plugin:: command:dev-test-eslint.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> CommandResult:
        with self._error_unexpected_recoverable(CalledProcessError):
            check_call(
                [
                    "node_modules/.bin/eslint",
                    "-c",
                    "eslint.config.ts",
                    "data",
                    "eslint.config.ts",
                ],
                shell=sys.platform.startswith("win32"),
            )
