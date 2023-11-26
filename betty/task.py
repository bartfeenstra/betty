from __future__ import annotations

import multiprocessing
import os
import queue
import threading
from collections.abc import MutableSequence, MutableMapping
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, Executor, as_completed
from contextlib import suppress
from types import TracebackType
from typing import Generic, Callable, Awaitable, Any, overload, TypeVar, Protocol

from typing_extensions import ParamSpec, Concatenate, TypeAlias

from betty.asyncio import sync, gather
from betty.error import serialize

TaskP = ParamSpec('TaskP')
TaskBatchContextT = TypeVar('TaskBatchContextT')
_UnownedT = TypeVar('_UnownedT')


class TaskError:
    pass


class TaskActivityClosed(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task activity has closed already.')


class TaskActivityNotStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task activity has not yet started.')


class TaskActivityStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task activity has started already.')


class TaskPoolBusy(TaskError, RuntimeError):
    def __init__(self, remaining_batch_count: int):
        super().__init__(f'This task pool is still busy with {remaining_batch_count} task batches.')


Task: TypeAlias = tuple[
    Callable[Concatenate['TaskBatch[TaskBatchContextT]', TaskP], Awaitable[None]],
    TaskP.args,
    TaskP.kwargs,
]


class _TaskActivity:
    def __init__(
        self,
        pool_batches: _TaskBatches,
        pool_cancel: threading.Event,
        cancel: threading.Event,
        start: threading.Event,
        finish: threading.Event,
    ):
        self._pool_batches = pool_batches
        self._pool_cancel = pool_cancel
        self._cancel = cancel
        self._start = start
        self._finish = finish

    async def cancel(self) -> None:
        self._cancel.set()
        self._start.clear()
        await self._close()

    async def _close(self) -> None:
        pass

    @property
    def cancelled(self) -> bool:
        if self._cancel.is_set():
            return True
        if self._pool_cancel.is_set():
            return True
        return False

    @property
    def started(self) -> bool:
        return self._start.is_set()

    @property
    def finished(self) -> bool:
        return self._finish.is_set()

    @property
    def open(self) -> bool:
        if self.cancelled:
            return False
        if self.finished:
            return False
        return True

    def _assert_open(self) -> None:
        if not self.open:
            raise TaskActivityClosed

    def _assert_started(self) -> None:
        if not self.started:
            raise TaskActivityNotStarted()

    def _assert_not_started(self) -> None:
        if self.started:
            raise TaskActivityStarted()


class _OwnedTaskActivity(_TaskActivity, Generic[_UnownedT]):
    async def __aenter__(self) -> _UnownedT:
        await self.start()
        reduced = self.__reduce__()
        return reduced[0](*reduced[1])  # type: ignore[no-any-return, operator]

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        if exc_val is not None:
            await self.cancel()
        await self.finish()

    async def start(self) -> None:
        self._assert_open()
        self._assert_not_started()
        self._start.set()

    async def finish(self):
        if not self.cancelled:
            self._assert_started()
        self._finish.set()
        await self._close()

    async def _close(self):
        self._start.clear()


class TaskBatch(_TaskActivity, Generic[TaskBatchContextT]):
    def __init__(
        self,
        batch_id: bytes,
        pool_batches: _TaskBatches,
        pool_cancel: threading.Event,
        logging_locale: str,
        context: TaskBatchContextT,
        task_queue: queue.Queue[Task[TaskBatchContextT, Any]],
        claims_lock: threading.Lock,
        claimed_task_ids: MutableSequence[bytes],
        error: _TaskBatchNamespace,
        cancel: threading.Event,
        start: threading.Event,
        finish: threading.Event,
    ):
        super().__init__(pool_batches, pool_cancel, cancel, start, finish)
        self._id = batch_id
        self._logging_locale = logging_locale
        self._context = context
        self._task_queue = task_queue
        self._claims_lock = claims_lock
        self._claimed_task_ids = claimed_task_ids
        self._error = error

    def __reduce__(self) -> Any:
        return TaskBatch, (
            self._id,
            self._pool_batches,
            self._pool_cancel,
            self._logging_locale,
            self._context,
            self._task_queue,
            self._claims_lock,
            self._claimed_task_ids,
            self._error,
            self._cancel,
            self._start,
            self._finish,
        )

    @property
    def context(self) -> TaskBatchContextT:
        return self._context

    @property
    def logging_locale(self) -> str:
        return self._logging_locale

    def _task_id_to_bytes(self, task_id: str) -> bytes:
        return task_id.encode('utf-8')

    def claim(self, task_id: str) -> bool:
        task_id_bytes = self._task_id_to_bytes(task_id)
        with self._claims_lock:
            if task_id_bytes in self._claimed_task_ids:
                return False
            self._claimed_task_ids.append(task_id_bytes)
            return True

    async def _close(self) -> None:
        # A batch may be cancelled before it is started, and thus before it is added to the batches registry.
        with suppress(KeyError):
            del self._pool_batches[self._id]

    def delegate(
        self,
        callable: Callable[Concatenate[TaskBatch[TaskBatchContextT], TaskP], Awaitable[None]],
        *args: TaskP.args,
        **kwargs: TaskP.kwargs,
    ) -> None:
        self._assert_open()
        self._task_queue.put((callable, args, kwargs))

    async def perform_tasks(self) -> None:
        while not self.cancelled:
            if self._pool_cancel.is_set():
                await self.cancel()
                return
            try:
                callable, args, kwargs = self._task_queue.get_nowait()
            except queue.Empty:
                if not self.open:
                    return
            else:
                try:
                    await callable(
                        self,
                        *args,
                        **kwargs,
                    )
                except BaseException as error:
                    await self.cancel()
                    self._error.error = serialize(error)
                # New tasks may take a while to be delegated or won't be delegated at all, so free some memory.
                del callable, args, kwargs


_TaskBatches: TypeAlias = MutableMapping[bytes, TaskBatch[Any]]


class _TaskBatchNamespace(Protocol):
    error: BaseException | None


class OwnedTaskBatch(TaskBatch[TaskBatchContextT], _OwnedTaskActivity[TaskBatch[TaskBatchContextT]], Generic[TaskBatchContextT]):
    def __init__(
        self,
        pool_batches: _TaskBatches,
        pool_cancel: threading.Event,
        logging_locale: str,
        context: TaskBatchContextT,
    ):
        error = multiprocessing.Manager().Namespace()
        error.error = None
        super().__init__(
            os.urandom(16),
            pool_batches,
            pool_cancel,
            logging_locale,
            context,
            multiprocessing.Manager().Queue(),
            multiprocessing.Manager().Lock(),
            multiprocessing.Manager().list(),
            error,
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
        )

    async def start(self) -> None:
        await super().start()
        self._pool_batches[self._id] = self

    async def _close(self):
        await super()._close()
        if self._error.error is not None:
            raise self._error.error


class _TaskPool(_TaskActivity):
    def __init__(
        self,
        logging_locale: str,
        pool_batches: _TaskBatches,
        pool_cancel: threading.Event,
        cancel: threading.Event,
        start: threading.Event,
        finish: threading.Event,
    ):
        super().__init__(pool_batches, pool_cancel, cancel, start, finish)
        self._logging_locale = logging_locale

    def __reduce__(self) -> tuple[
        type[_TaskPool],
        tuple[
            str,
            _TaskBatches,
            threading.Event,
            threading.Event,
            threading.Event,
            threading.Event,
        ],
    ]:
        return (
            _TaskPool,
            (
                self._logging_locale,
                self._pool_batches,
                self._pool_cancel,
                self._cancel,
                self._start,
                self._finish,
            )
        )

    async def _close(self) -> None:
        await super()._close()
        self._pool_cancel.set()

    @overload
    def batch(self) -> OwnedTaskBatch[None]:
        pass

    @overload
    def batch(self, context: TaskBatchContextT) -> OwnedTaskBatch[TaskBatchContextT]:
        pass

    def batch(self, context: Any = None):
        self._assert_open()
        return OwnedTaskBatch(
            self._pool_batches,
            self._pool_cancel,
            self._logging_locale,
            context,
        )


class _OwnedTaskPool(_TaskPool, _OwnedTaskActivity[_TaskPool]):
    _executor: Executor

    def __init__(self, concurrency: int, logging_locale: str):
        super().__init__(
            logging_locale,
            multiprocessing.Manager().dict(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
        )
        self._workers: list[Future[None]] = []
        self._concurrency = concurrency
        self._join_workers = multiprocessing.Manager().Event()

    def _assert_not_busy(self) -> None:
        remaining_other_batch_count = len(self._pool_batches)
        if remaining_other_batch_count:
            raise TaskPoolBusy(remaining_other_batch_count)

    def _new_executor(self) -> Executor:
        raise NotImplementedError

    async def start(self) -> None:
        await super().start()
        self._join_workers.clear()
        self._executor = self._new_executor()
        for _ in range(0, self._concurrency):
            self._workers.append(self._executor.submit(_Worker(
                self._pool_batches,
                self._pool_cancel,
                self._concurrency,
            )))

    async def _close(self) -> None:
        await super()._close()
        # @todo We cannot do this here in the owned pool.
        # @todo Instead, perhaps spin up a maintenance thread that waits until the pool_cancel event is set,
        # @todo then performs the actual pool closure work?
        # @todo
        # @todo
        # @todo
        self._join_workers.set()
        # @todo Must we cancel futures? We should only have as many workers (futures) as there are threads/processes in the pool.
        try:
            executor = self._executor
        except AttributeError:
            pass
        else:
            executor.shutdown(cancel_futures=True)
            del self._executor
        self._start.clear()
        for worker in as_completed(self._workers):
            worker.result()


class ThreadTaskPool(_OwnedTaskPool):
    def _new_executor(self) -> Executor:
        return ThreadPoolExecutor(max_workers=self._concurrency)


class ProcessTaskPool(_OwnedTaskPool):
    def _new_executor(self) -> Executor:
        return ProcessPoolExecutor(max_workers=self._concurrency)


class _Worker:
    def __init__(
        self,
        pool_batches: _TaskBatches,
        pool_cancel: threading.Event,
        async_concurrency: int,
    ):
        self._pool_batches = pool_batches
        self._pool_cancel = pool_cancel
        self._async_concurrency = async_concurrency

    @sync
    async def __call__(self) -> None:
        await gather(*(
            self._perform_tasks()
            for _ in range(0, self._async_concurrency)
        ))

    async def _perform_tasks(self) -> None:
        while not self._pool_cancel.is_set():
            for batch in [*self._pool_batches.values()]:
                await batch.perform_tasks()
            # New batches may take a while to be started or won't be started at all, so free some memory.
            del batch
