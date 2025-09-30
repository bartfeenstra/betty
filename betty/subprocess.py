"""
Provide a subprocess API.
"""

import os
import subprocess
from asyncio import create_subprocess_exec, create_subprocess_shell
from asyncio.subprocess import Process
from collections.abc import Sequence
from pathlib import Path
from subprocess import PIPE

from betty.locale.localizable import Plain, _
from betty.user import User


class SubprocessError(Exception):
    """
    Raised when a subprocess failed.
    """


class CalledSubprocessError(subprocess.CalledProcessError, SubprocessError):
    """
    Raised when a subprocess was successfully invoked, but subsequently failed during its own execution.
    """


class FileNotFound(FileNotFoundError, SubprocessError):
    """
    Raised when a command could not be found.
    """


async def run_process(
    runnee: Sequence[str], cwd: Path | None = None, shell: bool = False, *, user: User
) -> Process:
    """
    Run a command in a subprocess.

    :raise betty.subprocess.SubprocessError:
    """
    command = " ".join(runnee)
    await user.message_debug(
        _("Running subprocess `{command}`...").format(command=command)
    )

    try:
        if shell:
            process = await create_subprocess_shell(
                " ".join(runnee), cwd=cwd, stderr=PIPE, stdout=PIPE
            )
        else:
            process = await create_subprocess_exec(
                *runnee, cwd=cwd, stderr=PIPE, stdout=PIPE
            )
        stdout, stderr = await process.communicate()
    except FileNotFoundError as error:
        await user.message_debug(Plain(str(error)))
        raise FileNotFound(str(error)) from None

    if process.returncode == 0:
        return process

    stdout_str = "\n".join(stdout.decode().split(os.linesep))
    stderr_str = "\n".join(stderr.decode().split(os.linesep))

    if stdout_str:
        await user.message_debug(
            _("Subprocess `{command}` stdout:\n{stdout}").format(
                command=command, stdout=stdout_str
            )
        )
    if stderr_str:
        await user.message_debug(
            _("Subprocess `{command}` stderr:\n{stderr}").format(
                command=command, stderr=stderr_str
            )
        )

    assert process.returncode is not None
    raise CalledSubprocessError(
        process.returncode,
        " ".join(runnee),
        stdout_str,
        stderr_str,
    )
