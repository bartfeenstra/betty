import json
from asyncio import sleep
from concurrent.futures.thread import ThreadPoolExecutor
from os import path
from tempfile import TemporaryDirectory

from betty.functools import sync
from betty.scheduler import ExecutorScheduler, JoiningError
from betty.tests import TestCase


def _executor_scheduler_test_task(carrier_file_path: str, *args, **kwargs):
    with open(carrier_file_path, 'w') as f:
        json.dump([args, kwargs], f)


class ExecutorSchedulerTest(TestCase):
    @sync
    async def test_schedule(self):
        with TemporaryDirectory() as directory_path:
            carrier_file_path = path.join(directory_path, 'carrier')
            args = ['*']
            kwargs = {
                '*': {},
            }

            sut = ExecutorScheduler(ThreadPoolExecutor())
            await sut.schedule(_executor_scheduler_test_task, carrier_file_path, *args, **kwargs)
            await sleep(1)
            with open(carrier_file_path) as f:
                self.assertEquals('[["*"], {"*": {}}]', f.read())

    @sync
    async def test_join(self):
        def _task():
            pass

        sut = ExecutorScheduler(ThreadPoolExecutor())
        await sut.schedule(_task)
        await sut.join()
        with self.assertRaises(JoiningError):
            await sut.schedule(_task)
