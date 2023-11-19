import asyncio
import multiprocessing
import threading
from collections.abc import Callable, Awaitable
from concurrent.futures import ProcessPoolExecutor
from queue import Queue, Empty
from typing import TypeAlias

from betty.app import App
from betty.task import _TaskBatch, _Task


async def task(sentinel: threading.Event) -> None:
    print('TASK')
    # The program hangs right here in the asyncio.to_thread() call if the worker async concurrency is greater than 1.
    await asyncio.to_thread(subtask, sentinel)
    print('TASK DONE')


def subtask(sentinel: threading.Event) -> None:
    print('SUBTASK')
    sentinel.set()
    print('SUBTASK DONE')


WorkerQueueItem: TypeAlias = tuple[Callable[[threading.Event], Awaitable[None]], threading.Event]


class _Worker:
    def __init__(
        self,
        queue: Queue[WorkerQueueItem],
        join_workers_when_done: threading.Event,
        join_workers_immediately: threading.Event,
    ):
        self._queue = queue
        self._join_workers_when_done = join_workers_when_done
        self._join_workers_immediately = join_workers_immediately

    def __call__(self) -> None:
        print('WORKER START')
        with asyncio.Runner() as runner:
            runner.run(self._perform_tasks_concurrently())
        print('WORKER EXIT')

    async def _perform_tasks_concurrently(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for _ in range(
                0,
                # This is the async concurrency. If set to 1 (no async concurrency), the program completes just fine.
                # If this is set to any value higher than 1, the program hangs in task(), as documented in that function.
                2,
            ):
                tg.create_task(self._perform_tasks())

    async def _perform_tasks(self) -> None:
        while not self._join_workers_immediately.is_set():
            try:
                callable, sentinel = self._queue.get_nowait()
            except Empty:
                if self._join_workers_when_done.is_set():
                    return
            else:
                print('WORKER TASK')
                try:
                    await callable(sentinel)
                    print('WORKER TASK AWAITED')
                except BaseException as error:
                    print('WORKER TASK ERROR')
                    print(error)
                    raise
                finally:
                    self._queue.task_done()
                    print('WORKER TASK DONE')


async def main() -> None:
    sentinel = multiprocessing.Manager().Event()
    queue:Queue[WorkerQueueItem] = multiprocessing.Manager().Queue()
    join_workers_when_done = multiprocessing.Manager().Event()
    join_workers_immediately = multiprocessing.Manager().Event()
    workers = []
    with ProcessPoolExecutor() as pool:
        try:
            print('POOL ENTER')
            for _ in range(0, 3):
                workers.append(pool.submit(_Worker(queue, join_workers_when_done, join_workers_immediately)))
            print('POOL WORKERS STARTED')
            queue.put((task, sentinel))
            print('POOL QUEUE JOINING...')
            # @todo This will fail if the workers never get around to emptying the queue.
            # @todo We may need two Events. One to signal a successful completion, and that workers should shut down
            # @todo when they are done. The other to signal a shortcut exit of any kind (error, cancellation) upon which
            # @todo workers must exit as soon as possible.
            # @todo
            # @todo
            join_workers_when_done.set()
            print('POOL WORKERS JOINING...')
            for worker in workers:
                worker.result()
        finally:
            print('POOL EXIT')


    assert sentinel.is_set()
    print('ALL GOOD')


async def task_error(batch: _TaskBatch[None], sentinel: threading.Event) -> None:
    print('TASK ERROR')
    raise RuntimeError('TASK ERROR RAISED')


async def task_task(batch: _TaskBatch[None], sentinel: threading.Event) -> None:
    print('TASK')
    await asyncio.to_thread(subtask, sentinel)
    print('TASK DONE')


def task_subtask(batch: _TaskBatch[None], sentinel: threading.Event) -> None:
    print('SUBTASK')
    sentinel.set()
    print('SUBTASK DONE')


async def main_task_api() -> None:
    sentinel = multiprocessing.Manager().Event()
    app = App()
    async with app:
        async with app.thread_pool.batch() as batch:
            batch.delegate(task_error, sentinel)
    assert sentinel.is_set()
    print('ALL GOOD')

if __name__ == "__main__":
    asyncio.run(main_task_api())