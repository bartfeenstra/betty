from __future__ import annotations

import asyncio
import gc
import multiprocessing
import pickle
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Protocol, overload, cast, Literal, TypeAlias

import pytest

from betty.task import TaskGroup, TaskGroupContextT, TaskContextClosed, OwnedTaskGroup


async def task_success(group: TaskGroup[None], /, sentinel: threading.Event) -> None:
    sentinel.set()


async def task_success_executor(group: TaskGroup[None], /, sentinel: threading.Event) -> None:
    """
    Set a sentinel through an asyncio event loop executor.

    This catches certain problems when nesting APIs, where the program would freeze.
    """
    await asyncio.get_running_loop().run_in_executor(None, sentinel.set)


async def task_error(group: TaskGroup[None], /) -> None:
    raise TaskTestError


class TaskTestError(RuntimeError):
    pass


class TestTaskGroup:
    @overload
    def _sut(self, *, logging_locale: str = 'en', context: None = None) -> OwnedTaskGroup[None]:
        pass
    
    
    @overload
    def _sut(self, *, logging_locale: str = 'en', context: TaskGroupContextT) -> OwnedTaskGroup[TaskGroupContextT]:
        pass
    
    
    def _sut(self, *, logging_locale = 'en', context = None):
        return OwnedTaskGroup(  # type: ignore[return-value]
            multiprocessing.Manager().dict(),
            logging_locale,
            context,
        )

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_pickle(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        pickled_sut = pickle.dumps(sut)
        unpickled_sut = pickle.loads(pickled_sut)
        assert isinstance(unpickled_sut, TaskGroup)

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_context(self, pickled: bool) -> None:
        context = 'I am the context'
        sut = self._sut(context=context)
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        assert context == sut.context

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_logging_locale(self, pickled: bool) -> None:
        logging_locale = 'nl'
        sut = self._sut(logging_locale=logging_locale)
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        assert logging_locale == sut.logging_locale

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_claim(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        task_ids = ('task ID 1', 'task ID 2', 'task ID 3')
        for task_id in task_ids:
            assert sut.claim(task_id)
            assert not sut.claim(task_id)

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_delegate(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        sentinel = multiprocessing.Manager().Event()
        sut.delegate(task_success, sentinel)

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_delegate_when_cancelled(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        await sut.cancel()
        with pytest.raises(TaskContextClosed):
            sut.delegate(task_error)

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_delegate_when_finished(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        sut._close.set()
        with pytest.raises(TaskContextClosed):
            sut.delegate(task_error)

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_perform_tasks(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        sentinel1 = multiprocessing.Manager().Event()
        sentinel2 = multiprocessing.Manager().Event()
        sentinel3 = multiprocessing.Manager().Event()
        sut.delegate(task_success, sentinel1)
        sut.delegate(task_success, sentinel2)
        sut.delegate(task_success, sentinel3)
        sut._close.set()
        await sut.perform_tasks()
        assert sentinel1.is_set()
        assert sentinel2.is_set()
        assert sentinel3.is_set()

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_perform_tasks_with_cancellation(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        sentinel = multiprocessing.Manager().Event()
        for _ in range(0, 999):
            sut.delegate(task_success, sentinel)
        with ThreadPoolExecutor() as executor:
            executor.submit(sut.perform_tasks)
            await sut.cancel()

    @pytest.mark.parametrize('pickled', [
        True,
        False,
    ])
    async def test_perform_tasks_with_error(self, pickled: bool) -> None:
        sut = self._sut()
        if pickled:
            __owned_sut = sut
            sut = pickle.loads(pickle.dumps(sut))

        sentinel1 = multiprocessing.Manager().Event()
        sentinel2 = multiprocessing.Manager().Event()
        sut.delegate(task_success, sentinel1)
        sut.delegate(task_error)
        sut.delegate(task_success, sentinel2)
        sut._start.set()
        sut._close.set()
        await sut.perform_tasks()
        assert sentinel1.is_set()
        assert isinstance(sut._error.error, TaskTestError)


# class _TaskManagerTest:
#     _sut_cls: ClassVar[type[_OwnedTaskManager]]
#
#     def sut(self) -> _OwnedTaskManager:
#         return self._sut_cls(3, 'en')
#
#     async def test_pickle(self) -> None:
#         sut = self.sut()
#         async with sut:
#             pickle.loads(pickle.dumps(sut))
#
#     async def test_with_error_during_context_manager(self) -> None:
#         sut = self.sut()
#         with pytest.raises(RuntimeError):
#             async with sut:
#                 raise RuntimeError
#
#     async def test_start(self) -> None:
#         sut = self.sut()
#         await sut.start()
#         try:
#             with pytest.raises(TaskManagerStarted):
#                 await sut.start()
#         finally:
#             await sut.join()
#
#     async def test_join_not_started(self) -> None:
#         sut = self.sut()
#         with pytest.raises(TaskManagerNotStarted):
#             await sut.join()
#
#     async def test_join_is_busy(self) -> None:
#         sut = self.sut()
#         async with sut:
#             async with sut.group():
#                 with pytest.raises(TaskManagerBusy):
#                     await sut.join()
#
#     async def test_join_without_tasks(self) -> None:
#         sut = self.sut()
#         async with sut:
#             pass
#
#     async def test_group_delegate(self) -> None:
#         sut = self.sut()
#         group_pre_error_sentinel = multiprocessing.Manager().Event()
#         group_pre_error_executor_sentinel = multiprocessing.Manager().Event()
#         async with sut:
#             with pytest.raises(TaskTestError):
#                 async with sut.group() as group:
#                     group.delegate(task_success, group_pre_error_sentinel)
#                     group.delegate(task_success_executor, group_pre_error_executor_sentinel)
#                     group.delegate(task_error)
#
#         assert group_pre_error_sentinel.is_set()
#         assert group_pre_error_executor_sentinel.is_set()
#
#
# class TestThreadTaskManager(_TaskManagerTest):
#     _sut_cls = ThreadPoolTaskManager
#
#
# class TestProcessTaskManager(_TaskManagerTest):
#     _sut_cls = ProcessPoolTaskManager
