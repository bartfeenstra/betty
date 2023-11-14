import asyncio
import multiprocessing
import threading
from collections.abc import Callable, Awaitable
from concurrent.futures import ProcessPoolExecutor
from queue import Queue, Empty
from typing import TypeAlias


async def task(sentinel: threading.Event) -> None:
    print('TASK')
    await asyncio.to_thread(subtask, sentinel)
    # The program hangs right here if the worker async concurrency is greater than 1.
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
        join_workers: threading.Event,
    ):
        self._queue = queue
        self._join_workers = join_workers

    def __call__(self) -> None:
        print('WORKER START')
        with asyncio.Runner() as runner:
            # This fails.
            runner.run(self._perform_tasks_concurrently())
            # But doing the same, but without asyncio.gather(), means the program completes just fine.
            # runner.run(self._perform_tasks())
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
        while not self._join_workers.is_set():
            try:
                callable, sentinel = self._queue.get_nowait()
            except Empty:
                continue
            else:
                print('WORKER TASK')
                try:
                    await callable(sentinel)
                    print('WORKER TASK AWAITED')
                except BaseException as error:
                    print('WORKER TASK ERROR')
                    print(error)
                finally:
                    self._queue.task_done()
                    print('WORKER TASK DONE')


async def main() -> None:
    sentinel = multiprocessing.Manager().Event()
    queue:Queue[WorkerQueueItem] = multiprocessing.Manager().Queue()
    join_workers = multiprocessing.Manager().Event()
    workers = []
    with ProcessPoolExecutor() as pool:
        print('POOL ENTER')
        for _ in range(0, 3):
            workers.append(pool.submit(_Worker(queue, join_workers)))
        print('POOL WORKERS STARTED')
        queue.put((task, sentinel))
        print('POOL QUEUE JOINING...')
        queue.join()
        print('POOL WORKERS JOINING...')
        join_workers.set()
    try:
        for worker in workers:
            worker.result()
    finally:
        print('POOL EXIT')


    assert sentinel.is_set()
    print('ALL GOOD')

if __name__ == "__main__":
    asyncio.run(main())