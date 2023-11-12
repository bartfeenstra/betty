import logging
import os
import subprocess as stdsubprocess
from asyncio import subprocess
from textwrap import indent
from typing import Sequence, Any, Callable, Awaitable, ParamSpec


P = ParamSpec('P')


async def run_exec(runnee: Sequence[str], **kwargs: Any) -> subprocess.Process:
    return await _run(
        subprocess.create_subprocess_exec,
        runnee,
        runnee[0],
        *runnee[1:],
        **kwargs,
    )


async def run_shell(runnee: Sequence[str], **kwargs: Any) -> subprocess.Process:
    return await _run(
        subprocess.create_subprocess_shell,
        runnee,
        ' '.join(runnee),
        **kwargs,
    )


async def _run(
    runner: Callable[P, Awaitable[subprocess.Process]],
    runnee: Sequence[str],
    *args: P.args,
    **kwargs: P.kwargs,
) -> subprocess.Process:
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.PIPE
    process = await runner(*args, **kwargs)
    await process.wait()

    if process.returncode == 0:
        return process

    stdout = process.stdout
    stdout_str = '' if stdout is None else '\n'.join((await stdout.read()).decode().split(os.linesep))
    stderr = process.stderr
    stderr_str = '' if stderr is None else '\n'.join((await stderr.read()).decode().split(os.linesep))

    error = stdsubprocess.CalledProcessError(
        process.returncode,  # type: ignore[arg-type]
        ' '.join(runnee),
        stdout_str,
        stderr_str,
    )
    logging.getLogger().warning(
        f'{str(error)}\nSTDOUT:\n{indent(stdout_str, "    ")}\nSTDERR:{indent(stderr_str, "   ")}',
    )
    raise error
