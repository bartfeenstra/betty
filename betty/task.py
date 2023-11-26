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
TaskGroupContextT = TypeVar('TaskGroupContextT')
_UnownedT = TypeVar('_UnownedT')


class TaskError:
    pass


class TaskContextClosed(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task context has closed already.')


class TaskContextNotStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task context has not yet started.')


class TaskContextStarted(TaskError, RuntimeError):
    def __init__(self):
        super().__init__('This task context has started already.')


class TaskManagerBusy(TaskError, RuntimeError):
    def __init__(self, remaining_groups_count: int):
        super().__init__(f'This task manager is still busy with {remaining_groups_count} task groups.')


Task: TypeAlias = tuple[
    Callable[Concatenate['TaskGroup[TaskGroupContextT]', TaskP], Awaitable[None]],
    TaskP.args,
    TaskP.kwargs,
]


class _Base:
    def __init__(
        self,
        cancel: threading.Event,
        start: threading.Event,
        finish: threading.Event,
    ):
        self._cancel = cancel
        self._start = start
        self._finish = finish

    async def cancel(self) -> None:
        self._finish.set()
        self._cancel.set()
        self._start.clear()
        await self._close()

    async def _close(self) -> None:
        raise NotImplementedError

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

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
            raise TaskContextClosed

    def _assert_started(self) -> None:
        if not self.started:
            raise TaskContextNotStarted()

    def _assert_not_started(self) -> None:
        if self.started:
            raise TaskContextStarted()


class _OwnedBase(_Base, Generic[_UnownedT]):
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


class TaskGroup(_Base, Generic[TaskGroupContextT]):
    def __init__(
        self,
        group_id: bytes,
        groups: _TaskGroups,
        logging_locale: str,
        context: TaskGroupContextT,
        task_queue: queue.Queue[Task[TaskGroupContextT, Any]],
        claims_lock: threading.Lock,
        claimed_task_ids: MutableSequence[bytes],
        error: _TaskGroupNamespace,
        cancel: threading.Event,
        start: threading.Event,
        finish: threading.Event,
    ):
        super().__init__(cancel, start, finish)
        self._id = group_id
        self._groups = groups
        self._logging_locale = logging_locale
        self._context = context
        self._task_queue = task_queue
        self._claims_lock = claims_lock
        self._claimed_task_ids = claimed_task_ids
        self._error = error

    def __reduce__(self) -> Any:
        return TaskGroup, (
            self._id,
            self._groups,
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
    def context(self) -> TaskGroupContextT:
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
        # A group may be cancelled before it is started, and thus before it is added to the groups registry.
        with suppress(KeyError):
            del self._groups[self._id]

    def delegate(
        self,
        callable: Callable[Concatenate[TaskGroup[TaskGroupContextT], TaskP], Awaitable[None]],
        *args: TaskP.args,
        **kwargs: TaskP.kwargs,
    ) -> None:
        self._assert_open()
        self._task_queue.put((callable, args, kwargs))

    async def perform_tasks(self) -> None:
        while not self.cancelled:
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


_TaskGroups: TypeAlias = MutableMapping[bytes, TaskGroup[Any]]


class _TaskGroupNamespace(Protocol):
    error: BaseException | None


class OwnedTaskGroup(TaskGroup[TaskGroupContextT], _OwnedBase[TaskGroup[TaskGroupContextT]], Generic[TaskGroupContextT]):
    def __init__(
        self,
        groups: _TaskGroups,
        logging_locale: str,
        context: TaskGroupContextT,
    ):
        error = multiprocessing.Manager().Namespace()
        error.error = None
        super().__init__(
            os.urandom(16),
            groups,
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
        self._groups[self._id] = self

    async def _close(self):
        await super()._close()
        if self._error.error is not None:
            raise self._error.error


class _TaskManager(_Base):
    def __init__(
        self,
        logging_locale: str,
        groups: _TaskGroups,
        cancel: threading.Event,
        start: threading.Event,
        finish: threading.Event,
    ):
        super().__init__(cancel, start, finish)
        self._logging_locale = logging_locale
        self._groups = groups

    def __reduce__(self) -> tuple[
        type[_TaskManager],
        tuple[
            str,
            _TaskGroups,
            threading.Event,
            threading.Event,
            threading.Event,
        ],
    ]:
        return (
            _TaskManager,
            (
                self._logging_locale,
                self._groups,
                self._cancel,
                self._start,
                self._finish,
            )
        )

    async def cancel(self) -> None:
        await super().cancel()
        await gather(*(
            group.cancel()
            for group
            in self._groups.values()
        ))

    @overload
    def group(self) -> OwnedTaskGroup[None]:
        pass

    @overload
    def group(self, context: TaskGroupContextT) -> OwnedTaskGroup[TaskGroupContextT]:
        pass

    def group(self, context: Any = None):
        self._assert_open()
        return OwnedTaskGroup(
            self._groups,
            self._logging_locale,
            context,
        )


class _OwnedTaskManager(_TaskManager, _OwnedBase[_TaskManager]):
    _executor: Executor

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
        self._join_workers = multiprocessing.Manager().Event()

    def _assert_not_busy(self) -> None:
        remaining_other_group_count = len(self._groups)
        if remaining_other_group_count:
            raise TaskManagerBusy(remaining_other_group_count)

    def _new_executor(self) -> Executor:
        raise NotImplementedError

    async def start(self) -> None:
        await super().start()
        self._join_workers.clear()
        self._executor = self._new_executor()
        for _ in range(0, self._concurrency):
            self._workers.append(self._executor.submit(_Worker(
                self._groups,
                self._concurrency,
                self._join_workers,
            )))

    async def _close(self) -> None:
        await super()._close()
        self._join_workers.set()
        # @todo Must we cancel futures? We should only have as many workers (futures) as there are threads/processes in the pool.
        self._executor.shutdown(cancel_futures=True)
        del self._executor
        self._start.clear()
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
        groups: _TaskGroups,
        async_concurrency: int,
        join_workers: threading.Event,
    ):
        self._groups = groups
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
            for group in [*self._groups.values()]:
                await group.perform_tasks()
            # New groups may take a while to be started or won't be started at all, so free some memory.
            del group
