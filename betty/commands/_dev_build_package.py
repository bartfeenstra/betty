from __future__ import annotations

import re
import sys
from subprocess import CalledProcessError, check_call
from typing import TYPE_CHECKING, final, override

from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition("dev-build-package", label="Build Betty as a Python package")
class DevBuildPackage(DevCommand):
    """
    .. plugin:: command:dev-build-package.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        parser.add_argument("version", action="store")
        return self._command_function

    async def _command_function(self, *, version: str) -> CommandResult:
        with open("pyproject.toml", encoding="utf-8") as f:
            original_pyproject = f.read()
        versioned_pyproject = re.sub(
            r"^version = '0.0.0'$",
            f"version = '{version}'",
            original_pyproject,
            flags=re.MULTILINE,
        )
        with open("pyproject.toml", encoding="utf-8", mode="w") as f:
            f.write(versioned_pyproject)
        try:
            with self._error_unexpected_recoverable(CalledProcessError):
                check_call([sys.executable, "-m", "build"])
                check_call(["twine", "check", "dist/*"])
        finally:
            with open("pyproject.toml", encoding="utf-8", mode="w") as f:
                f.write(original_pyproject)
