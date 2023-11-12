from __future__ import annotations

import asyncio
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


class Task(Generic[TaskBatchContextT, TaskP]):
    def __init__(
        self,
        callable: Callable[Concatenate[_TaskBatch[TaskBatchContextT], TaskP], Awaitable[None]],
        *args: TaskP.args,
        **kwargs: TaskP.kwargs,
    ):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs


class _TaskBatch(Generic[TaskBatchContextT]):
    def __init__(
        self,
        logging_locale: str,
        context: TaskBatchContextT = None,  # type: ignore[assignment]
        shared_state: _TaskBatchSharedState[TaskBatchContextT] | None = None,
    ):
        self._logging_locale = logging_locale
        self._context = context
        if shared_state is None:
            self._task_queue = multiprocessing.Manager().Queue()
            self._claims_lock = multiprocessing.Manager().Lock()
            self._claimed_task_ids: MutableSequence[bytes] = multiprocessing.Manager().list()
            self.__error: _TaskBatchNamespace = multiprocessing.Manager().Namespace()
            self.__error.error = None
        else:
            (
                self._task_queue,
                self._claims_lock,
                self._claimed_task_ids,
                self.__error,
            ) = shared_state

    def __reduce__(self) -> Any:
        return _TaskBatch, (
            self._logging_locale,
            self._context,
            (
                self._task_queue,
                self._claims_lock,
                self._claimed_task_ids,
                self.__error,
            ),
        )

    @property
    def context(self) -> TaskBatchContextT:
        return self._context

    @property
    def _error(self) -> BaseException | None:
        return self.__error.error

    @_error.setter
    def _error(self, error: BaseException) -> None:
        self.__error.error = serialize(error)

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

    def delegate(self, task: Task[TaskBatchContextT, Any]) -> None:
        self._task_queue.put(task)

    async def _perform_tasks(self) -> None:
        while True:
            try:
                task = self._task_queue.get_nowait()
            except queue.Empty:
                return
            else:
                try:
                    await task.callable(
                        self,
                        *task.args,
                        **task.kwargs,
                    )
                except BaseException as error:
                    self._error = error
                finally:
                    self._task_queue.task_done()


_TaskBatches: TypeAlias = MutableMapping[bytes, _TaskBatch[Any]]


class _TaskBatchNamespace(Protocol):
    error: BaseException | None


_TaskBatchSharedState: TypeAlias = tuple[
    queue.Queue[Task[TaskBatchContextT, Any]],
    threading.Lock,
    MutableSequence[bytes],
    _TaskBatchNamespace,
]


class _OwnedTaskBatch(_TaskBatch[TaskBatchContextT], Generic[TaskBatchContextT]):
    def __init__(
        self,
        logging_locale: str,
        batches: _TaskBatches,
        context: TaskBatchContextT = None,  # type: ignore[assignment]
        shared_state: _TaskBatchSharedState[TaskBatchContextT] | None = None,
    ):
        self._id = os.urandom(16)
        self._started = False
        self._batches = batches
        super().__init__(logging_locale, context, shared_state)

    async def __aenter__(self) -> _TaskBatch[TaskBatchContextT]:
        await self.start()
        return _TaskBatch(*self.__reduce__()[1])

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        if exc_val is not None:
            self._error = exc_val
        await self.join()

    def _assert_started(self) -> None:
        if not self._started:
            raise TaskBatchNotStarted()

    def _assert_not_started(self) -> None:
        if self._started:
            raise TaskBatchStarted()

    async def start(self) -> None:
        self._assert_not_started()
        self._started = True
        self._batches[self._id] = self

    async def join(self):
        print(f'{self} JOINING')
        self._assert_started()
        print(f'{self} JOIN QUEUE')
        await asyncio.get_running_loop().run_in_executor(None, self._task_queue.join)
        del self._batches[self._id]
        self._started = False
        print(f'{self} JOINED')
        if self._error is not None:
            raise self._error from None


class _TaskManager:
    def __init__(
        self,
        logging_locale: str,
        batches: _TaskBatches,
    ):
        self._logging_locale = logging_locale
        self._batches = batches

    def __reduce__(self) -> tuple[
        type[_TaskManager],
        tuple[
            str,
            _TaskBatches,
        ],
    ]:
        return (
            _TaskManager,
            (
                self._logging_locale,
                self._batches,
            )
        )

    @overload
    def batch(self) -> _OwnedTaskBatch[None]:
        pass

    @overload
    def batch(self, context: TaskBatchContextT) -> _OwnedTaskBatch[TaskBatchContextT]:
        pass

    def batch(self, context: Any = None):
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

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        await self.join()

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
        # @todo We never seem to reach this during the tests...
        print(f'{self} JOINING')
        self._assert_started()
        self._assert_not_busy()
        print(f'{self} JOINING WORKERS')
        self._join_workers.set()
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
        print('WORKER START ASYNC PERFORMER')
        while not self._join_workers.is_set():
            # @todo
            # print('WORKER NOT READY TO JOIN...')
            for batch in [*self._batches.values()]:
                await batch._perform_tasks()
        print('WORKER EXIT ASYNC PERFORMER')
