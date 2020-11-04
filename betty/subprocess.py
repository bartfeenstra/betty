import subprocess as stdsubprocess
from tempfile import TemporaryFile


def run(*args, **kwargs) -> stdsubprocess.CompletedProcess:
    with TemporaryFile() as f:
        kwargs['stdout'] = f
        kwargs['stderr'] = f
        process = stdsubprocess.run(*args, **kwargs)
        if process.returncode != 0:
            f.seek(0)
            raise RuntimeError(f.read().decode('utf-8'))
        return process
