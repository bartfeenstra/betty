"""
Test utilities for :py:mod:`betty.console`.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, final

from betty.console import ExitCode, main

if TYPE_CHECKING:
    from betty.app import App


@final
@dataclass
class Result:
    """
    A console run result.
    """

    exit_code: int
    stderr: str
    stdout: str


async def run(app: App, *args: str, exit_code: ExitCode = ExitCode.OK) -> Result:
    """
    Run a Betty console command.
    """
    stderr_f = StringIO()
    stdout_f = StringIO()
    with redirect_stderr(stderr_f), redirect_stdout(stdout_f):
        try:
            await main(app, args)
        except SystemExit as exception:
            if exception.code is None:
                actual_exit_code = 0  # pragma: no cover
            elif isinstance(exception.code, int):
                actual_exit_code = exception.code
            else:
                actual_exit_code = 1  # pragma: no cover
        except BaseException as error:  # pragma: no cover
            raise AssertionError(f"The console did not raise {SystemExit}") from error
        else:  # pragma: no cover
            raise AssertionError(f"The console did not raise {SystemExit}")

    stderr_f.seek(0)
    stderr = stderr_f.read()
    stdout_f.seek(0)
    stdout = stdout_f.read()

    assert actual_exit_code == exit_code, f"""
The Betty command `{" ".join(args)}` unexpectedly exited with code {actual_exit_code}, but {exit_code} was expected.
Stdout:
{stdout}
Stderr:
{stderr}
"""
    return Result(actual_exit_code, stderr, stdout)
