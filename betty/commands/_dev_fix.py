from __future__ import annotations

from subprocess import CalledProcessError, check_call
from typing import TYPE_CHECKING, final, override

from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition("dev-fix", label="Run Betty's tests")
class DevFix(DevCommand):
    """
    .. plugin:: command:dev-fix.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> CommandResult:
        try:
            # Fix Python code style violations.
            check_call(["ruff", "check", "--preview", "--fix", "."])
            check_call(["ruff", "format", "--preview", "."])

            # Fix CSS code style violations.
            check_call([
                "node_modules/.bin/stylelint",
                "--fix",
                "betty/**/*.css",
                "betty/**/*.scss",
            ])

            # Fix JS code style violations.
            check_call([
                "node_modules/.bin/eslint",
                "--fix",
                "-c",
                "eslint.config.ts",
                "data",
                "eslint.config.ts",
            ])
        except CalledProcessError:
            return
