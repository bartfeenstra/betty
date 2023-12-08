from __future__ import annotations

import asyncio
import multiprocessing
import pickle
import threading

import pytest

from betty.task import TaskBatch, TaskActivityClosed, ThreadTaskPool, ProcessTaskPool, _OwnedTaskPool, _TaskPool, \
    TaskPoolBusy


async def task_success(batch: TaskBatch[None], /, sentinel: threading.Event) -> None:
    sentinel.set()


async def task_success_executor(batch: TaskBatch[None], /, sentinel: threading.Event) -> None:
    """
    Set a sentinel through an asyncio event loop executor.

    This catches certain problems when nesting APIs, where the program would freeze.
    """
    await asyncio.get_running_loop().run_in_executor(None, sentinel.set)


async def task_error(batch: TaskBatch[None], /) -> None:
    raise TaskTestError


class TaskTestError(RuntimeError):
    pass


class TestTaskPool:
    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_pickle(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            pickled_sut = pickle.dumps(sut)
            unpickled_sut = pickle.loads(pickled_sut)
            assert isinstance(unpickled_sut, _TaskPool)

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_cancel(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            async with sut.batch() as batch:
                await sut.cancel()

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_finish_when_busy(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            async with sut.batch():
                with pytest.raises(TaskPoolBusy):
                    await sut.finish()

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_with_error_during_context_manager(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            with pytest.raises(RuntimeError):
                raise RuntimeError

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_pickle(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            async with sut.batch() as batch:
                pickled_batch = pickle.dumps(batch)
                unpickled_batch = pickle.loads(pickled_batch)
                assert isinstance(unpickled_batch, TaskBatch)

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_context(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            context = 'I am the context'
            async with sut.batch(context=context) as batch:
                assert context == batch.context

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_logging_locale(self, sut_cls: type[_OwnedTaskPool]) -> None:
        logging_locale = 'nl'
        sut = sut_cls(3, logging_locale)
        async with sut:
            async with sut.batch() as batch:
                assert logging_locale == batch.logging_locale

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_claim(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            async with sut.batch() as batch:
                task_ids = ('task ID 1', 'task ID 2', 'task ID 3')
                for task_id in task_ids:
                    assert batch.claim(task_id)
                    assert not batch.claim(task_id)

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_delegate(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        sentinel = multiprocessing.Manager().Event()
        sentinel_executor = multiprocessing.Manager().Event()
        async with sut:
            async with sut.batch() as batch:
                batch.delegate(task_success, sentinel)
                batch.delegate(task_success_executor, sentinel_executor)
        assert sentinel.is_set()
        assert sentinel_executor.is_set()

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_delegate_when_cancelled(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            async with sut.batch() as batch:
                await sut.cancel()
                with pytest.raises(TaskActivityClosed):
                    batch.delegate(task_error)

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_delegate_when_finished(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        async with sut:
            async with sut.batch() as batch:
                pass
            with pytest.raises(TaskActivityClosed):
                batch.delegate(task_error)

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_cancel(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        sentinel = multiprocessing.Manager().Event()
        async with sut:
            async with sut.batch() as batch:
                for _ in range(0, 999):
                    batch.delegate(task_success, sentinel)
                await sut.cancel()

    @pytest.mark.parametrize('sut_cls', [
        ThreadTaskPool,
        ProcessTaskPool,
    ])
    async def test_batch_with_task_error(self, sut_cls: type[_OwnedTaskPool]) -> None:
        sut = sut_cls(3, 'en')
        sentinel1 = multiprocessing.Manager().Event()
        sentinel2 = multiprocessing.Manager().Event()
        async with sut:
            with pytest.raises(TaskTestError):
                async with sut.batch() as batch:
                    batch.delegate(task_success, sentinel1)
                    batch.delegate(task_error)
                    batch.delegate(task_success, sentinel2)
        assert sentinel1.is_set()
