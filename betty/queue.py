import asyncio
from typing import Callable


class IsJoiningError(RuntimeError):
    def __init__(self):
        RuntimeError.__init__(self, 'This queue is currently joining.')


class Queue:
    async def put(self, task: Callable) -> None:
        raise NotImplementedError

    async def consume(self) -> None:
        raise NotImplementedError

    async def join(self) -> None:
        raise NotImplementedError


class SetQueue(Queue):
    def __init__(self):
        self._seen = set()
        self._queue = asyncio.Queue()
        self._joining = False
        self._consumers = None

    async def put(self, task: Callable) -> None:
        if self._joining:
            raise IsJoiningError()
        if self._joining or task not in self._seen:
            self._seen.add(task)
            await self._queue.put(task)

    async def consume(self) -> None:
        if self._consumers is None:
            self._consumers = [asyncio.create_task(self._consumer()) for _ in range(9)]

    async def _consumer(self):
        while True:
            task = await self._queue.get()
            await task()
            self._queue.task_done()

    async def join(self) -> None:
        if self._joining:
            raise IsJoiningError()
        self._joining = True
        await self.consume()
        await self._queue.join()
        self._seen.clear()
        self._joining = False
        for consumer in self._consumers:
            consumer.cancel()
