from __future__ import annotations

import asyncio
import multiprocessing
import pickle
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import ClassVar

import pytest

from betty.task import _TaskBatch, ThreadPoolTaskManager, ProcessPoolTaskManager, TaskManagerBusy, _OwnedTaskManager, \
    TaskManagerNotStarted, TaskManagerStarted, TaskBatchContextT, TaskContextNotActive


async def task_success(batch: _TaskBatch[None], /, sentinel: threading.Event) -> None:
    sentinel.set()


async def task_success_executor(batch: _TaskBatch[None], /, sentinel: threading.Event) -> None:
    """
    Set a sentinel through an asyncio event loop executor.

    This catches certain problems when nesting APIs, where the program would freeze.
    """
    await asyncio.get_running_loop().run_in_executor(None, sentinel.set)


async def task_error(batch: _TaskBatch[None], /) -> None:
    raise TaskTestError


class TaskTestError(RuntimeError):
    pass


class TestTaskBatch:
    def _sut(self, *, logging_locale: str = 'en', context: TaskBatchContextT | None = None) -> _TaskBatch[TaskBatchContextT]:
        return _TaskBatch(
            logging_locale,
            context,
            multiprocessing.Manager().Queue(),
            multiprocessing.Manager().Lock(),
            multiprocessing.Manager().list(),
            multiprocessing.Manager().Namespace(),
            multiprocessing.Manager().Event(),
            multiprocessing.Manager().Event(),
        )

    async def test_pickle(self) -> None:
        sut = self._sut()
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        assert isinstance(unpickled_sut, _TaskBatch)

    async def test_context(self) -> None:
        context = 'I am the context'
        sut = self._sut(context=context)
        assert context is sut.context

    async def test_logging_locale(self) -> None:
        logging_locale = 'en'
        sut = self._sut(logging_locale=logging_locale)
        assert logging_locale is sut.logging_locale

    async def test_claim(self) -> None:
        task_ids = ('task ID 1', 'task ID 2', 'task ID 3')
        sut = self._sut()
        for task_id in task_ids:
            assert sut.claim(task_id)
            assert not sut.claim(task_id)

    async def test_delegate(self) -> None:
        sut = self._sut()
        sentinel = multiprocessing.Manager().Event()
        sut.delegate(task_success, sentinel)

    async def test_delegate_when_cancelled(self) -> None:
        sut = self._sut()
        await sut.cancel()
        with pytest.raises(TaskContextNotActive):
            sut.delegate(task_error)

    async def test_delegate_when_finished(self) -> None:
        sut = self._sut()
        sut._finish.set()
        with pytest.raises(TaskContextNotActive):
            sut.delegate(task_error)

    async def test_perform_tasks(self) -> None:
        sut = self._sut()
        sentinel1 = multiprocessing.Manager().Event()
        sentinel2 = multiprocessing.Manager().Event()
        sentinel3 = multiprocessing.Manager().Event()
        sut.delegate(task_success, sentinel1)
        sut.delegate(task_success, sentinel2)
        sut.delegate(task_success, sentinel3)
        sut._finish.set()
        await sut.perform_tasks()
        assert sentinel1.is_set()
        assert sentinel2.is_set()
        assert sentinel3.is_set()

    async def test_perform_tasks_with_cancellation(self) -> None:
        sut = self._sut()
        sentinel = multiprocessing.Manager().Event()
        for _ in range(0, 999):
            sut.delegate(task_success, sentinel)
        with ThreadPoolExecutor() as executor:
            executor.submit(sut.perform_tasks)
            await sut.cancel()

    async def test_perform_tasks_with_error(self) -> None:
        sut = self._sut()
        sentinel1 = multiprocessing.Manager().Event()
        sentinel2 = multiprocessing.Manager().Event()
        sut.delegate(task_success, sentinel1)
        sut.delegate(task_error)
        sut.delegate(task_success, sentinel2)
        sut._finish.set()
        await sut.perform_tasks()
        assert sentinel1.is_set()
        assert isinstance(sut._error.error, TaskTestError)


class _TaskManagerTest:
    _sut_cls: ClassVar[type[_OwnedTaskManager]]

    def sut(self) -> _OwnedTaskManager:
        return self._sut_cls(3, 'en')

    async def test_pickle(self) -> None:
        sut = self.sut()
        async with sut:
            pickle.loads(pickle.dumps(sut))

    async def test_with_error_during_context_manager(self) -> None:
        sut = self.sut()
        with pytest.raises(RuntimeError):
            async with sut:
                raise RuntimeError

    async def test_start(self) -> None:
        sut = self.sut()
        await sut.start()
        try:
            with pytest.raises(TaskManagerStarted):
                await sut.start()
        finally:
            await sut.join()

    async def test_join_not_started(self) -> None:
        sut = self.sut()
        with pytest.raises(TaskManagerNotStarted):
            await sut.join()

    async def test_join_is_busy(self) -> None:
        sut = self.sut()
        async with sut:
            async with sut.batch():
                with pytest.raises(TaskManagerBusy):
                    await sut.join()

    async def test_join_without_tasks(self) -> None:
        sut = self.sut()
        async with sut:
            pass

    async def test_batch_delegate(self) -> None:
        sut = self.sut()
        batch_pre_error_sentinel = multiprocessing.Manager().Event()
        batch_pre_error_executor_sentinel = multiprocessing.Manager().Event()
        async with sut:
            with pytest.raises(TaskTestError):
                async with sut.batch() as batch:
                    batch.delegate(task_success, batch_pre_error_sentinel)
                    batch.delegate(task_success_executor, batch_pre_error_executor_sentinel)
                    batch.delegate(task_error)

        assert batch_pre_error_sentinel.is_set()
        assert batch_pre_error_executor_sentinel.is_set()


class TestThreadTaskManager(_TaskManagerTest):
    _sut_cls = ThreadPoolTaskManager


class TestProcessTaskManager(_TaskManagerTest):
    _sut_cls = ProcessPoolTaskManager
