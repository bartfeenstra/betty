"""
Test utilities for :py:mod:`betty.console`.
"""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from typing import TypeVar, final

from betty.app import App
from betty.console import SystemExitCode, main

_T = TypeVar("_T")


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
    app: App, *args: str, expected_exit_code: SystemExitCode = SystemExitCode.OK
) -> Result:
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
