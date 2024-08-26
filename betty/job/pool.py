"""
Run jobs concurrently in a process pool.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import pickle
import queue
from asyncio import run, CancelledError, sleep, to_thread, create_task
from concurrent import futures
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import suppress, ExitStack
from math import floor
from typing import (
    Callable,
    MutableSequence,
    Self,
    Concatenate,
    Any,
    TYPE_CHECKING,
    ParamSpec, TypeVar, Generic,
)

from betty.asyncio import gather
from betty.job import Context
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project
    from types import TracebackType
    import threading


_ContextT = TypeVar("_ContextT", bound=Context)
_PoolTaskP = ParamSpec("_PoolTaskP")

worker_setup: Callable[[], None] | None = None


@internal
class Pool(Generic[_ContextT]):
    """
    Set up a worker process, before the worker starts performing tasks.

    This may be used to modify the environment, set up mocks, etc.
    """

    def __init__(self, project: Project):
        self._project = project
        self._queue = multiprocessing.Manager().Queue()
        self._cancel = multiprocessing.Manager().Event()
        self._finish = multiprocessing.Manager().Event()
        self._exit_stack = ExitStack()
        self._executor: Executor | None = None
        self._workers: MutableSequence[futures.Future[None]] = []
        # @todo Ensure this is synchronized across processes.
        self._count_total = 0

    async def __aenter__(self) -> Self:
        try:
            await self._start()
        except BaseException:
            self._cancel.set()
            await self._stop()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_val is None:
            self._finish.set()
        else:
            self._cancel.set()
        await self._stop()
        if exc_val is None:
            await self._log_jobs()

    async def _start(self) -> None:
        concurrency = os.cpu_count() or 2
        # @todo Remove this. For now, this lets us go wild during testing without having to worry about
        # @todo machines freezing because all their cores are busy.
        concurrency = 2
        executor = ProcessPoolExecutor(max_workers=concurrency)
        # We check that the futures are complete in self.__aexit__().
        self._exit_stack.callback(
            lambda: executor.shutdown(wait=False, cancel_futures=True)
        )
        pickled_app = pickle.dumps(self._project.app)
        pickled_reduced_project = pickle.dumps(self._project.reduce())
        for _ in range(0, concurrency):
            self._workers.append(
                executor.submit(
                    _PoolWorker(
                        self._queue,
                        self._cancel,
                        self._finish,
                        concurrency,
                        # This is an optional, pickleable callable that can be set during a test.
                        # All we do here is to ensure each worker has access to it.
                        worker_setup,
                        pickled_app=pickled_app,
                        pickled_reduced_project=pickled_reduced_project,
                    )
                )
            )
        log_task = create_task(self._log_jobs_forever())
        self._exit_stack.callback(log_task.cancel)

    async def _stop(self) -> None:
        await to_thread(self._wait_workers)
        await to_thread(self._exit_stack.close)

    def _wait_workers(self) -> None:
        for worker in futures.as_completed(self._workers):
            worker.result()

    async def _log_jobs(self) -> None:
        total_job_count = self._count_total
        completed_job_count = total_job_count - self._queue.qsize()
        logging.getLogger(__name__).info(
            self._project.app.localizer._(
                "Generated {completed_job_count} out of {total_job_count} items ({completed_job_percentage}%)."
            ).format(
                completed_job_count=completed_job_count,
                total_job_count=total_job_count,
                completed_job_percentage=floor(
                    completed_job_count / (total_job_count / 100)
                    if total_job_count > 0
                    else 0
                ),
            )
        )

    async def _log_jobs_forever(self) -> None:
        with suppress(CancelledError):
            while True:
                await self._log_jobs()
                await sleep(5)

    def delegate(
        self,
        task_callable: Callable[
            Concatenate[_ContextT, _PoolTaskP], Any
        ],
        *task_args: _PoolTaskP.args,
        **task_kwargs: _PoolTaskP.kwargs,
    ) -> None:
        self._queue.put((task_callable, task_args, task_kwargs))
        self._count_total += 1


class _PoolWorker:
    def __init__(
        self,
        task_queue: queue.Queue[
            tuple[
                Callable[
                    Concatenate[_ContextT, _PoolTaskP], Any
                ],
                _PoolTaskP.args,
                _PoolTaskP.kwargs,
            ]
        ],
        cancel: threading.Event,
        finish: threading.Event,
        async_concurrency: int,
        setup: Callable[[], None] | None,
        *,
        pickled_app: bytes,
        pickled_reduced_project: bytes,
    ):
        self._task_queue = task_queue
        self._cancel = cancel
        self._finish = finish
        self._setup = setup
        self._async_concurrency = async_concurrency
        self._pickled_app = pickled_app
        self._pickled_reduced_project = pickled_reduced_project

    def __call__(self) -> None:
        if self._setup is not None:
            self._setup()
        run(self._perform_tasks_concurrently())

    async def _perform_tasks_concurrently(self) -> None:
        app = pickle.loads(self._pickled_app)
        reduced_project = pickle.loads(self._pickled_reduced_project)
        async with app, reduced_project(app) as project:
            # @todo Allow contexts to be pickled
            # @todo GenerationContext (and in the future maybe Load and PostLoad contexts) as well as Extension
            # @todo must all be pickleable and all must be unreduceable by simply providing a Project.
            # @todo Can we reuse `ProjectDependentFactory` for this? Maybe not, because ProjectDependentFactory returns Self.
            # @todo What about a plain Callable[[Project], _T] signature?
            # @todo
            # @todo
            job_context = GenerationContext(project)
            await gather(
                *(
                    self._perform_tasks(job_context)
                    for _ in range(0, self._async_concurrency)
                )
            )

    async def _perform_tasks(self, job_context: _ContextT) -> None:
        while not self._cancel.is_set():
            try:
                task_callable, task_args, task_kwargs = self._task_queue.get_nowait()
            except queue.Empty:
                if self._finish.is_set():
                    return
            else:
                await task_callable(
                    job_context,
                    *task_args,
                    **task_kwargs,
                )
