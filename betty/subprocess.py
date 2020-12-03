import subprocess as stdsubprocess


def run(args, *remaining_args, **kwargs) -> stdsubprocess.CompletedProcess:
    kwargs['stdout'] = stdsubprocess.PIPE
    kwargs['stderr'] = stdsubprocess.PIPE
    process = stdsubprocess.run(args, *remaining_args, **kwargs)
    if process.returncode != 0:
        raise stdsubprocess.CalledProcessError(process.returncode, args, process.stdout, process.stderr)
    return process
