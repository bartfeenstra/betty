"""
Provide a subprocess API.
"""

import logging
import os
from asyncio import create_subprocess_exec, create_subprocess_shell
from asyncio.subprocess import Process
from pathlib import Path
from subprocess import CalledProcessError, PIPE
from traceback import format_exception


async def run_process(
    runnee: list[str],
    cwd: Path | None = None,
    shell: bool = False,
) -> Process:
    """
    Run a command in a subprocess.
    """
    command = " ".join(runnee)
    logger = logging.getLogger(__name__)
    logger.debug(f"Running subprocess `{command}`...")

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
    except BaseException as error:
        logger.debug(
            f'Subprocess `{command}` raised an error:\n{" ".join(format_exception(error))}'
        )
        raise

    if process.returncode == 0:
        return process

    stdout_str = "\n".join(stdout.decode().split(os.linesep))
    stderr_str = "\n".join(stderr.decode().split(os.linesep))

    if stdout_str:
        logger.debug(f"Subprocess `{command}` stdout:\n{stdout_str}")
    if stderr_str:
        logger.debug(f"Subprocess `{command}` stderr:\n{stderr_str}")

    assert process.returncode is not None
    raise CalledProcessError(
        process.returncode,
        " ".join(runnee),
        stdout_str,
        stderr_str,
    )
