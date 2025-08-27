"""
Test utilities for :py:mod:`betty.cli`.
"""

from typing import IO, Any

from asyncclick.testing import CliRunner, Result

from betty.app import App
from betty.cli import new_main_command


async def run(
    app: App,
    *args: str,
    expected_exit_code: int = 0,
    input: str | bytes | IO[Any] | None = None,  # noqa A002
) -> Result:
    """
    Run a Betty CLI command.
    """
    runner = CliRunner()
    result = await runner.invoke(
        await new_main_command(app), args, catch_exceptions=False, input=input
    )
    assert result.exit_code == expected_exit_code, f"""
The Betty command `{" ".join(args)}` unexpectedly exited with code {result.exit_code}, but {expected_exit_code} was expected.
Stdout:
{result.stdout}
Stderr:
{result.stderr}
"""
    return result
