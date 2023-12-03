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
        batches: _TaskBatches,
        cancel: threading.Event,
        finish: threading.Event,
        joined: threading.Event,
    ):
        self._batches = batches
        self._cancel = cancel
        self._finish = finish
        self._joined = joined

    async def cancel(self) -> None:
        self._cancel.set()
        self._join()

    def _join(self) -> None:
        self._joined.set()

    # @todo Do we need all these properties still?
    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    @property
    def finished(self) -> bool:
        return self._finish.is_set()

    @property
    def closed(self) -> bool:
        return self.cancelled or self.finished

    @property
    def joined(self) -> bool:
        return self._joined.is_set()

    def _assert_not_closed(self) -> None:
        if self.closed:
            raise TaskActivityClosed


class _OwnedTaskActivity(_TaskActivity, Generic[_UnownedT]):
    async def __aenter__(self) -> _UnownedT:
        reduced = self.__reduce__()
        return reduced[0](*reduced[1])  # type: ignore[no-any-return, operator]

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        if exc_val is None:
            await self.finish()
        await self.cancel()

    async def finish(self) -> None:
        self._finish.set()
        self._joined.wait()


class TaskBatch(_TaskActivity, Generic[TaskBatchContextT]):
    def __init__(
        self,
        batch_id: bytes,
        batches: _TaskBatches,
        logging_locale: str,
        context: TaskBatchContextT,
        task_queue: queue.Queue[Task[TaskBatchContextT, Any]],
        claims_lock: threading.Lock,
        claimed_task_ids: MutableSequence[bytes],
        error: _TaskBatchNamespace,
        cancel: threading.Event,
        finish: threading.Event,
        joined: threading.Event,
    ):
        super().__init__(batches, cancel, finish, joined)
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
            self._batches,
            self._logging_locale,
            self._context,
            self._task_queue,
            self._claims_lock,
            self._claimed_task_ids,
            self._error,
            self._cancel,
            self._finish,
            self._joined,
        )

    def _join(self) -> None:
        super()._join()
        with suppress(KeyError):
            del self._batches[self._id]

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
        callable: Callable[Concatenate[TaskBatch[TaskBatchContextT], TaskP], Awaitable[None]],
        *args: TaskP.args,
        **kwargs: TaskP.kwargs,
    ) -> None:
        self._assert_not_closed()
        self._task_queue.put((callable, args, kwargs))

    async def perform_tasks(self) -> None:
        while not self.joined:
            try:
                callable, args, kwargs = self._task_queue.get_nowait()
            except queue.Empty:
                if self.closed:
                    self._join()
                return
            else:
                try:
                    await callable(
                        self,
                        *args,
                        **kwargs,
                    )
                except BaseException as error:
                    self._error.error = serialize(error)
                    await self.cancel()
                # New tasks may take a while to be delegated or won't be delegated at all, so free some memory.
                del callable, args, kwargs


_TaskBatches: TypeAlias = MutableMapping[bytes, TaskBatch[Any]]


class _TaskBatchNamespace(Protocol):
    error: BaseException | None


class OwnedTaskBatch(TaskBatch[TaskBatchContextT], _OwnedTaskActivity[TaskBatch[TaskBatchContextT]], Generic[TaskBatchContextT]):
    def __init__(
        self,
        batches: _TaskBatches,
        logging_locale: str,
        context: TaskBatchContextT,
    ):
        error = multiprocessing.Manager().Namespace()
        error.error = None
        super().__init__(
            os.urandom(16),
            batches,
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
        self._register()

    def _register(self) -> None:
        self._batches[self._id] = self

    async def finish(self) -> None:
        await super().finish()
        if self._error.error is not None:
            raise self._error.error


class _TaskPool(_TaskActivity):
    def __init__(
        self,
        logging_locale: str,
        batches: _TaskBatches,
        cancel: threading.Event,
        should_finish: threading.Event,
        joined: threading.Event,
    ):
        super().__init__(batches, cancel, should_finish, joined)
        self._logging_locale = logging_locale

    def __reduce__(self) -> tuple[
        type[_TaskPool],
        tuple[
            str,
            _TaskBatches,
            threading.Event,
            threading.Event,
            threading.Event,
        ],
    ]:
        return (
            _TaskPool,
            (
                self._logging_locale,
                self._batches,
                self._cancel,
                self._finish,
                self._joined,
            )
        )

    async def cancel(self) -> None:
        for batch in self._batches.values():
            await batch.cancel()
        await super().cancel()

    @overload
    def batch(self) -> OwnedTaskBatch[None]:
        pass

    @overload
    def batch(self, context: TaskBatchContextT) -> OwnedTaskBatch[TaskBatchContextT]:
        pass

    def batch(self, context: Any = None):
        self._assert_not_closed()
        return OwnedTaskBatch(
            self._batches,
            self._logging_locale,
            context,
        )


class _OwnedTaskPool(_TaskPool, _OwnedTaskActivity[_TaskPool]):
    def __init__(self, concurrency: int, logging_locale: str):
        super().__init__(
            logging_locale,
            multiprocessing.Manager().dict(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
        )
        self._workers: list[Future[None]] = []
        self._concurrency = concurrency
        self._executor = self._new_executor()
        for _ in range(0, self._concurrency):
            self._workers.append(self._executor.submit(_Worker(
                self._batches,
                self._cancel,
                self._finish,
                self._concurrency,
            )))

    def _assert_not_busy(self) -> None:
        remaining_other_batch_count = len(self._batches)
        if remaining_other_batch_count:
            raise TaskPoolBusy(remaining_other_batch_count)

    def _new_executor(self) -> Executor:
        raise NotImplementedError

    async def finish(self) -> None:
        self._assert_not_busy()
        self._join()
        await super().finish()
        self._executor.shutdown()
        del self._executor
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
        batches: _TaskBatches,
        cancel: threading.Event,
        finish: threading.Event,
        async_concurrency: int,
    ):
        self._batches = batches
        self._cancel = cancel
        self._finish = finish
        self._async_concurrency = async_concurrency

    @sync
    async def __call__(self) -> None:
        await gather(*(
            self._perform_tasks()
            for _ in range(0, self._async_concurrency)
        ))

    async def _perform_tasks(self) -> None:
        while True:
            if self._cancel.is_set():
                return
            if self._finish.is_set() and not self._batches:
                return

            for batch in [*self._batches.values()]:
                await batch.perform_tasks()
                # New batches may take a while to be created or won't be created at all, so free some memory.
                del batch
