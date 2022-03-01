from asyncio.subprocess import Process
from subprocess import CalledProcessError

from betty import subprocess
from betty.asyncio import sync
from betty.tests import TestCase


class RunExecTest(TestCase):
    @sync
    async def test_without_errors(self):
        process = await subprocess.run_exec(['true'])
        self.assertIsInstance(process, Process)

    @sync
    async def test_with_errors(self):
        with self.assertRaises(CalledProcessError):
            await subprocess.run_exec(['false'])


class RunShellTest(TestCase):
    @sync
    async def test_without_errors(self):
        process = await subprocess.run_shell(['true'])
        self.assertIsInstance(process, Process)

    @sync
    async def test_with_errors(self):
        with self.assertRaises(CalledProcessError):
            await subprocess.run_shell(['false'])
