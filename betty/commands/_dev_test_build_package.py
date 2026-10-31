from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CalledProcessError, check_call, check_output
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, final, override

from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition("dev-test-build-package", label="Test the Betty package build")
class DevTestBuildPackage(DevCommand):
    """
    .. plugin:: command:dev-test-build-package.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> CommandResult:
        version = "0.0.0a0"
        with self._error_unexpected_recoverable(CalledProcessError):
            check_call(["betty", "dev-build-package", version])
        wheel_path = f"dist/betty-{version}-py3-none-any.whl"
        venv_bin = "Scripts" if sys.platform.startswith("win32") else "bin"
        with (
            TemporaryDirectory() as working_directory_str,
            self._error_unexpected_recoverable(CalledProcessError),
        ):
            working_directory = Path(working_directory_str)
            check_call(
                [sys.executable, "-m", "virtualenv", "venv"], cwd=working_directory
            )
            check_call([
                str(working_directory / "venv" / venv_bin / "pip"),
                "install",
                wheel_path,
            ])
            output = check_output([
                str(working_directory / "venv" / venv_bin / "betty"),
                "about",
            ]).decode(sys.stdout.encoding)
        assert version in output
