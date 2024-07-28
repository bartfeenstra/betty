"""
Test utilities for :py:mod:`betty.cli`.
"""

from typing import IO, Any

from click.testing import Result, CliRunner

from betty.cli import main


def run(
    *args: str,
    expected_exit_code: int = 0,
    input: str | bytes | IO[Any] | None = None,  # noqa A002
) -> Result:
    """
    Run a Betty CLI command.
    """
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, args, catch_exceptions=False, input=input)
    if result.exit_code != expected_exit_code:
        raise AssertionError(
            f"""
The Betty command `{" ".join(args)}` unexpectedly exited with code {result.exit_code}, but {expected_exit_code} was expected.
Stdout:
{result.stdout}
Stderr:
{result.stderr}
"""
        )
    return result
