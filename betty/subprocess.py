import subprocess as stdsubprocess


def run(*args, **kwargs) -> stdsubprocess.CompletedProcess:
    kwargs['capture_output'] = True
    process = stdsubprocess.run(*args, **kwargs)
    if process.returncode != 0:
        raise RuntimeError(process.stdout.decode('utf-8'))
    return process
