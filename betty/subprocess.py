import logging
import os
import subprocess as stdsubprocess
from asyncio import subprocess
from textwrap import indent
from typing import Sequence


async def run_exec(runnee: Sequence[str], **kwargs) -> subprocess.Process:
    return await _run(
        subprocess.create_subprocess_exec,
        runnee,
        runnee[0],
        *runnee[1:],
        **kwargs,
    )


async def run_shell(runnee: Sequence[str], **kwargs) -> subprocess.Process:
    return await _run(
        subprocess.create_subprocess_shell,
        runnee,
        ' '.join(runnee),
        **kwargs,
    )


async def _run(runner, runnee: Sequence[str], *args, **kwargs) -> subprocess.Process:
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.PIPE
    process = await runner(*args, **kwargs)
    await process.wait()

    if process.returncode == 0:
        return process

    stdout = '\n'.join((await process.stdout.read()).decode().split(os.linesep))
    stderr = '\n'.join((await process.stderr.read()).decode().split(os.linesep))
    error = stdsubprocess.CalledProcessError(
        process.returncode,
        ' '.join(runnee),
        stdout,
        stderr,
    )
    logging.getLogger().warning(f'{str(error)}\nSTDOUT:\n{indent(stdout, "    ")}\nSTDERR:{indent(stderr, "   ")}')
    raise error
