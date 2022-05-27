from asyncio.subprocess import Process
from subprocess import CalledProcessError

import pytest

from betty import subprocess


class TestRunExec:
    async def test_without_errors(self):
        process = await subprocess.run_exec(['true'])
        assert isinstance(process, Process)

    async def test_with_errors(self):
        with pytest.raises(CalledProcessError):
            await subprocess.run_exec(['false'])


class TestRunShell:
    async def test_without_errors(self):
        process = await subprocess.run_shell(['true'])
        assert isinstance(process, Process)

    async def test_with_errors(self):
        with pytest.raises(CalledProcessError):
            await subprocess.run_shell(['false'])
