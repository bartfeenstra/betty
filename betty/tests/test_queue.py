from asyncio import sleep
from unittest import TestCase

from betty.functools import sync
from betty.queue import SetQueue


class SetQueueTest(TestCase):
    @sync
    async def test_put(self):
        carrier = []
        task = lambda: carrier.append(True)
        sut = SetQueue()
        await sut.put(task)
        await sleep(1)
        self.assertNotIn(True, carrier)

    @sync
    async def test_consume(self):
        carrier = []

        async def _task():
            carrier.append(True)
        sut = SetQueue()
        await sut.put(_task)
        await sut.consume()
        await sleep(1)
        try:
            self.assertIn(True, carrier)
        finally:
            await sut.join()

    @sync
    async def test_join(self):
        carrier = []

        async def _task():
            carrier.append(True)
        sut = SetQueue()
        await sut.put(_task)
        await sut.join()
        self.assertIn(True, carrier)
