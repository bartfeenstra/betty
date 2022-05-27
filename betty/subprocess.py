import subprocess as stdsubprocess
from asyncio import subprocess
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
    kwargs.setdefault('stdout', subprocess.DEVNULL)
    kwargs.setdefault('stderr', subprocess.DEVNULL)
    process = await runner(*args, **kwargs)
    await process.wait()
    if process.returncode == 0:
        return process
    raise stdsubprocess.CalledProcessError(
        process.returncode,
        ' '.join(runnee),
        process.stdout,
        process.stderr,
    )
