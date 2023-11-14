from __future__ import annotations

import asyncio
import multiprocessing
import pickle
import threading
from typing import ClassVar

import pytest

from betty.task import _TaskBatch, ThreadPoolTaskManager, ProcessPoolTaskManager, TaskManagerBusy, Task, \
    _OwnedTaskManager, TaskManagerNotStarted, TaskManagerStarted


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
                    batch.delegate(Task(task_success, batch_pre_error_sentinel))
                    batch.delegate(Task(task_success_executor, batch_pre_error_executor_sentinel))
                    batch.delegate(Task(task_error))

        assert batch_pre_error_sentinel.is_set()
        assert batch_pre_error_executor_sentinel.is_set()


class TestThreadTaskManager(_TaskManagerTest):
    _sut_cls = ThreadPoolTaskManager


class TestProcessTaskManager(_TaskManagerTest):
    _sut_cls = ProcessPoolTaskManager
