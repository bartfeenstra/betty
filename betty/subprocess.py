"""
Provide a subprocess API.
"""

import logging
import os
import subprocess
import sys
from asyncio import create_subprocess_exec, create_subprocess_shell
from asyncio.subprocess import Process
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

from betty.typing import internal


class SubprocessError(Exception):
    """
    Raised when a subprocess failed.
    """

    pass


class CalledSubprocessError(subprocess.CalledProcessError, SubprocessError):
    """
    Raised when a subprocess was successfully invoked, but subsequently failed during its own execution.
    """

    pass


class FileNotFound(FileNotFoundError, SubprocessError):
    """
    Raised when a command could not be found.
    """

    pass


async def run_process(
    runnee: Sequence[str],
    cwd: Path | None = None,
    shell: bool = False,
) -> Process:
    """
    Run a command in a subprocess.

    :raise betty.subprocess.SubprocessError:
    """
    command = " ".join(runnee)
    logger = logging.getLogger(__name__)
    logger.debug(f"Running subprocess `{command}`...")

    try:
        if shell:
            process = await create_subprocess_shell(
                " ".join(runnee),
                cwd=cwd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
        else:
            process = await create_subprocess_exec(
                *runnee, cwd=cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
            )
        stdout, stderr = await process.communicate()
    except FileNotFoundError as error:
        logger.debug(str(error))
        raise FileNotFound(str(error)) from None

    if process.returncode == 0:
        return process

    stdout_str = "\n".join(stdout.decode().split(os.linesep))
    stderr_str = "\n".join(stderr.decode().split(os.linesep))

    if stdout_str:
        logger.debug(f"Subprocess `{command}` stdout:\n{stdout_str}")
    if stderr_str:
        logger.debug(f"Subprocess `{command}` stderr:\n{stderr_str}")

    assert process.returncode is not None
    raise CalledSubprocessError(
        process.returncode,
        " ".join(runnee),
        stdout_str,
        stderr_str,
    )


@internal
async def run_process_in_terminal(
    runnee: Sequence[str], cwd: Path | None = None
) -> Process:
    """
    Run a command in a subprocess in a new terminal window.

    :raise betty.subprocess.SubprocessError:
    """
    # @todo macOS too
    # Windows.
    if sys.platform.startswith("win32"):
        return await run_process(["cmd.exe", "/k", *runnee], cwd=cwd)
    # Linux.
    else:
        commands = [
            ["gnome-terminal", "--", *runnee],
            ["xterm", "-e", *runnee],
        ]
        for command in commands:
            with suppress(FileNotFoundError):
                return await run_process(command, cwd=cwd)
        terminals = [command[0] for command in commands]
        raise FileNotFound(
            f"Could not launch any of the following terminals: {terminals}"
        )
