from __future__ import annotations

import multiprocessing
import os
import queue
import threading
from collections.abc import MutableSequence, MutableMapping
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, Executor, as_completed
from types import TracebackType
from typing import Generic, Callable, Awaitable, Any, overload, TypeVar, Protocol

from typing_extensions import ParamSpec, Concatenate, TypeAlias

from betty.asyncio import sync, gather
from betty.error import serialize

TaskP = ParamSpec('TaskP')
TaskBatchContextT = TypeVar('TaskBatchContextT')


class TaskError:
    pass


class TaskContextNotActive(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task context is not active.')


class TaskBatchNotStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task batch has not yet started.')


class TaskBatchStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task batch has started already.')


class TaskManagerNotStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task manager has not yet started.')


class TaskManagerStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task manager has started already.')


class TaskManagerBusy(TaskError, RuntimeError):
    def __init__(self, remaining_batch_count: int):
        super().__init__(f'This task manager is still busy with {remaining_batch_count} batches.')


# @todo Turn this into a type alias for a tuple
class _Task(Generic[TaskBatchContextT, TaskP]):
    def __init__(
        self,
        callable: Callable[Concatenate[_TaskBatch[TaskBatchContextT], TaskP], Awaitable[None]],
        *args: TaskP.args,
        **kwargs: TaskP.kwargs,
    ):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs


class _TaskContext:
    def __init__(
        self,
        cancel: threading.Event,
        finish: threading.Event,
    ):
        self._cancel = cancel
        self._finish = finish

    async def cancel(self) -> None:
        self._cancel.set()

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    @property
    def finished(self) -> bool:
        return self._finish.is_set()

    @property
    def active(self) -> bool:
        if self.cancelled:
            return False
        if self.finished:
            return False
        return True

    def _assert_active(self) -> None:
        if not self.active:
            raise TaskContextNotActive



class _TaskBatch(_TaskContext, Generic[TaskBatchContextT]):
    def __init__(
        self,
        logging_locale: str,
        context: TaskBatchContextT | None,
        task_queue: queue.Queue,
        claims_lock: threading.Lock,
        claimed_task_ids: MutableSequence[bytes],
        error: _TaskBatchNamespace,
        cancel: threading.Event,
        finish: threading.Event,
    ):
        super().__init__(cancel, finish)
        self._logging_locale = logging_locale
        self._context = context
        self._task_queue = task_queue
        self._claims_lock = claims_lock
        self._claimed_task_ids = claimed_task_ids
        self._error = error

    def __reduce__(self) -> Any:
        return _TaskBatch, (
            self._logging_locale,
            self._context,
            self._task_queue,
            self._claims_lock,
            self._claimed_task_ids,
            self._error,
            self._cancel,
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

    def delegate(
        self,
        callable: Callable[Concatenate[_TaskBatch[TaskBatchContextT], TaskP], Awaitable[None]],
        *args: TaskP.args,
        **kwargs: TaskP.kwargs,
    ) -> None:
        self._assert_active()
        self._task_queue.put(_Task(callable, *args, **kwargs))

    async def perform_tasks(self) -> None:
        while not self._cancel.is_set():
            try:
                task = self._task_queue.get_nowait()
            except queue.Empty:
                if self._finish.is_set():
                    return
            else:
                try:
                    await task.callable(
                        self,
                        *task.args,
                        **task.kwargs,
                    )
                    self._task_queue.task_done()
                except BaseException as error:
                    await self.cancel()
                    self._error.error = serialize(error)


_TaskBatches: TypeAlias = MutableMapping[bytes, _TaskBatch[Any]]


class _TaskBatchNamespace(Protocol):
    error: BaseException | None


class _OwnedTaskBatch(_TaskBatch[TaskBatchContextT], Generic[TaskBatchContextT]):
    def __init__(
        self,
        logging_locale: str,
        batches: _TaskBatches,
        context: TaskBatchContextT | None = None,
    ):
        self._id = os.urandom(16)
        self._started = False
        self._batches = batches
        super().__init__(
            logging_locale,
            context,
            multiprocessing.Manager().Queue(),
            multiprocessing.Manager().Lock(),
            multiprocessing.Manager().list(),
            multiprocessing.Manager().Namespace(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
        )

    async def __aenter__(self) -> _TaskBatch[TaskBatchContextT]:
        await self.start()
        return _TaskBatch(*self.__reduce__()[1])

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        if exc_val is not None:
            await self.cancel()
            self._error.error = serialize(exc_val)
        await self.join()

    def _assert_started(self) -> None:
        if not self._started:
            raise TaskBatchNotStarted()

    def _assert_not_started(self) -> None:
        if self._started:
            raise TaskBatchStarted()

    async def cancel(self) -> None:
        await super().cancel()
        # @todo Same as for task managers, what if the non-owned batch is cancelled?
        # @todo Even if we put .cancel() on the owned instances only, the concept of cancellation
        # @todo is relevant if a non-owned task batch catches an error too, though
        # @todo
        # @todo
        del self._batches[self._id]

    async def start(self) -> None:
        self._assert_not_started()
        self._started = True
        self._batches[self._id] = self

    async def join(self):
        self._assert_started()
        self._finish.set()
        del self._batches[self._id]
        if self._error.error is not None:
            raise self._error.error


class _TaskManager(_TaskContext):
    def __init__(
        self,
        logging_locale: str,
        batches: _TaskBatches,
        cancel: threading.Event,
        finish: threading.Event,
    ):
        super().__init__(cancel, finish)
        self._logging_locale = logging_locale
        self._batches = batches

    def __reduce__(self) -> tuple[
        type[_TaskManager],
        tuple[
            str,
            _TaskBatches,
            threading.Event,
            threading.Event,
        ],
    ]:
        return (
            _TaskManager,
            (
                self._logging_locale,
                self._batches,
                self._cancel,
                self._finish,
            )
        )

    async def cancel(self) -> None:
        await super().cancel()
        for batch in self._batches.values():
            await batch.cancel()

    @overload
    def batch(self) -> _OwnedTaskBatch[None]:
        pass

    @overload
    def batch(self, context: TaskBatchContextT) -> _OwnedTaskBatch[TaskBatchContextT]:
        pass

    def batch(self, context: Any = None):
        self._assert_active()
        return _OwnedTaskBatch(
            self._logging_locale,
            self._batches,
            context,
        )


class _OwnedTaskManager(_TaskManager):
    _executor: Executor

    def __init__(self, concurrency: int, logging_locale: str):
        super().__init__(
            logging_locale,
            multiprocessing.Manager().dict(),
        )
        self._started = False
        self._workers: list[Future[None]] = []
        self._concurrency = concurrency
        self._join_workers = multiprocessing.Manager().Event()

    async def __aenter__(self) -> _TaskManager:
        await self.start()
        return _TaskManager(*self.__reduce__()[1])

    async def __aexit__(self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: TracebackType | None) -> None:
        if exc_val is None:
            await self.join()
        else:
            await self._join_unchecked()

    def _assert_started(self) -> None:
        if not self._started:
            raise TaskManagerNotStarted()

    def _assert_not_started(self) -> None:
        if self._started:
            raise TaskManagerStarted()

    def _assert_not_busy(self) -> None:
        remaining_other_batch_count = len(self._batches)
        if remaining_other_batch_count:
            raise TaskManagerBusy(remaining_other_batch_count)

    def _new_executor(self) -> Executor:
        raise NotImplementedError

    async def cancel(self) -> None:
        # @todo This may be problematic/.
        # @todo If in another process, a reduced _TaskManager.cancel() is called, this then never propagates to the _OwnedTaskManager
        # @todo
        await super().cancel()
        await self._join_unchecked()

    async def start(self) -> None:
        self._assert_not_started()
        self._started = True
        self._join_workers.clear()
        self._executor = self._new_executor()
        for _ in range(0, self._concurrency):
            self._workers.append(self._executor.submit(_Worker(
                self._batches,
                self._concurrency,
                self._join_workers,
            )))

    async def join(self) -> None:
        self._assert_started()
        self._assert_not_busy()
        await self._join_unchecked()

    async def _join_unchecked(self) -> None:
        self._join_workers.set()
        # @todo Must we cancel futures? We should only have as many workers (futures) as there are threads/processes in the pool.
        self._executor.shutdown(cancel_futures=True)
        del self._executor
        self._started = False
        for worker in as_completed(self._workers):
            worker.result()


class ThreadPoolTaskManager(_OwnedTaskManager):
    def _new_executor(self) -> Executor:
        return ThreadPoolExecutor(max_workers=self._concurrency)


class ProcessPoolTaskManager(_OwnedTaskManager):
    def _new_executor(self) -> Executor:
        return ProcessPoolExecutor(max_workers=self._concurrency)


class _Worker:
    def __init__(
        self,
        batches: _TaskBatches,
        async_concurrency: int,
        join_workers: threading.Event,
    ):
        self._batches = batches
        self._async_concurrency = async_concurrency
        self._join_workers = join_workers

    @sync
    async def __call__(self) -> None:
        await gather(*(
            self._perform_tasks()
            for _ in range(0, self._async_concurrency)
        ))

    async def _perform_tasks(self) -> None:
        while not self._join_workers.is_set():
            for batch in [*self._batches.values()]:
                await batch.perform_tasks()
