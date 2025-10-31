"""
Test utilities for :py:mod:`betty.job.scheduler`.
"""

from __future__ import annotations

from asyncio import create_task, sleep
from collections.abc import Iterator, MutableSequence
from typing import TYPE_CHECKING, Generic, Self, TypeVar, cast, final

import pytest
from typing_extensions import override

from betty.job import Context, Job
from betty.job.executor.asyncio import AsyncExecutor
from betty.job.scheduler import (
    Cancelled,
    Closed,
    Completed,
    CyclicDependencyError,
    DuplicateJobError,
    Released,
    ScheduledJobBatch,
    Scheduler,
    UnknownJobError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


class StaticScheduler(Generic[_ContextCoT], Scheduler[_ContextCoT]):
    """
    A scheduler that issues static job batches.
    """

    def __init__(
        self, context: _ContextCoT, batches: Sequence[ScheduledJobBatch | Closed]
    ):
        self._context = context
        self._batches: Iterable[ScheduledJobBatch | Closed] | Closed = iter(batches)

    @override
    async def get(self) -> ScheduledJobBatch:
        if isinstance(self._batches, Closed):
            raise self._batches
        try:
            batch = next(cast(Iterator[ScheduledJobBatch | Closed], self._batches))
        except StopIteration:
            self._batches = Completed()
            raise self._batches from None
        else:
            if isinstance(batch, Closed):
                self._batches = batch
                raise batch
            return batch

    @override
    async def add(self, *jobs: Job[_ContextCoT]) -> None:
        raise NotImplementedError

    @override
    async def release(self) -> None:
        raise NotImplementedError

    @override
    async def cancel(self, reason: BaseException | None = None) -> None:
        raise NotImplementedError

    @override
    async def complete(self) -> None:
        while not isinstance(self._batches, Closed):
            await sleep(0)
        if not isinstance(self._batches, Completed):
            raise self._batches

    @override
    @property
    def context(self) -> _ContextCoT:
        return self._context


class SchedulerTestBaseContext(Context):
    """
    A job context for :py:class:`betty.test_utils.job.scheduler.SchedulerTestBase`.
    """

    def __init__(self):
        super().__init__()
        self.jobs: MutableSequence[Job[Self]] = []


_SchedulerTestBaseContextCoT = TypeVar(
    "_SchedulerTestBaseContextCoT", bound=SchedulerTestBaseContext, covariant=True
)


class _Job(Job[_SchedulerTestBaseContextCoT]):
    def __init__(
        self,
        job_id: str,
        *,
        additional_jobs: Sequence[_Job[_SchedulerTestBaseContextCoT]] | None = None,
        dependencies: set[str] | None = None,
        dependents: set[str] | None = None,
        priority: bool = False,
    ):
        super().__init__(
            job_id, dependencies=dependencies, dependents=dependents, priority=priority
        )
        self._additional_jobs = additional_jobs

    @override
    async def do(self, scheduler: Scheduler[_SchedulerTestBaseContextCoT], /) -> None:
        if self._additional_jobs is not None:
            for additional_job in self._additional_jobs:
                await scheduler.add(additional_job)
        scheduler.context.jobs.append(self)


@final
class Sleep(Job[_SchedulerTestBaseContextCoT]):
    """
    A job that sleeps for a long, long time.
    """

    @override
    async def do(self, scheduler: Scheduler[_SchedulerTestBaseContextCoT], /) -> None:
        await sleep(999999999)


class SchedulerTestBase(Generic[_SchedulerTestBaseContextCoT]):
    """
    A base class for testing :py:class:`betty.job.scheduler.Scheduler` implementations.
    """

    @pytest.fixture
    def sut(self) -> Scheduler[_SchedulerTestBaseContextCoT]:
        """
        Provide the systems under test.
        """
        raise NotImplementedError

    async def test___aexit___with_exception(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.__aexit__` implementations.
        """
        exception = RuntimeError()
        with pytest.raises(type(exception)) as exc_info:
            async with sut:
                raise exception
        assert exc_info.value is exception

    async def test_add(self, sut: Scheduler[_SchedulerTestBaseContextCoT]) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.add` implementations.
        """
        await sut.add(_Job("job"))

    async def test_add__with_duplicate_job(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.add` implementations.
        """
        await sut.add(_Job("job"))
        with pytest.raises(DuplicateJobError):
            await sut.add(_Job("job"))

    async def test_add__with_dependent_post_release(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.add` implementations.
        """
        await sut.release()
        with pytest.raises(Released):
            await sut.add(
                _Job("dependent"), _Job("dependency", dependents={"dependent"})
            )

    async def test_release(self, sut: Scheduler[_SchedulerTestBaseContextCoT]) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.release` implementations.
        """
        await sut.release()
        await sut.complete()

    @pytest.mark.parametrize(
        ("expected", "pre_release_jobs", "post_release_jobs"),
        [
            # No jobs.
            ([], [], []),
            # Isolated jobs.
            (
                ["isolated"],
                [],
                [
                    _Job("isolated"),
                ],
            ),
            (
                {f"isolated:{index}" for index in range(999)},
                [],
                [_Job(f"isolated:{index}") for index in range(999)],
            ),
            # A simple dependency, provided in different orders.
            (
                ["dependency", "dependent"],
                [],
                [
                    _Job("dependency"),
                    _Job("dependent", dependencies={"dependency"}),
                ],
            ),
            (
                ["dependency", "dependent"],
                [],
                [
                    _Job("dependent", dependencies={"dependency"}),
                    _Job("dependency"),
                ],
            ),
            # A simple dependent.
            (
                ["dependency", "dependent"],
                [
                    _Job("dependency", dependents={"dependent"}),
                ],
                [
                    _Job("dependent"),
                ],
            ),
            # One job adding another, isolated job
            (
                ["one", "other"],
                [],
                [_Job("one", additional_jobs=[_Job("other")])],
            ),
            # Diamond-shaped dependencies.
            (
                {"one", "two-one", "two-two", "three"},
                [],
                [
                    _Job("one"),
                    _Job("two-one", dependencies={"one"}),
                    _Job("two-two", dependencies={"one"}),
                    _Job("three", dependencies={"two-one", "two-two"}),
                ],
            ),
            # One job adding another job as a dependent by being its dependency.
            (
                ["dependency", "dependent"],
                [],
                [
                    _Job(
                        "dependency",
                        additional_jobs=[
                            _Job(
                                "dependent",
                                dependencies={"dependency"},
                            )
                        ],
                    )
                ],
            ),
            # Multiple jobs that must be run in a different order due to durations.
            (
                ["priority", "no-priority"],
                [],
                [
                    _Job("no-priority", priority=False),
                    _Job("priority", priority=True),
                ],
            ),
        ],
    )
    async def test_get__returns_job(
        self,
        expected: set[str] | Sequence[str],
        pre_release_jobs: Sequence[Job[_SchedulerTestBaseContextCoT]],
        post_release_jobs: Sequence[Job[_SchedulerTestBaseContextCoT]],
        sut: Scheduler[_SchedulerTestBaseContextCoT],
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        async with AsyncExecutor(sut):
            await sut.add(*pre_release_jobs)
            await sut.release()
            await sut.add(*post_release_jobs)
            await sut.complete()

        actual_ids = (job.id for job in sut.context.jobs)
        actual = set(actual_ids) if isinstance(expected, set) else list(actual_ids)
        assert actual == expected

    async def test_get__raises_when_unknown_dependency(
        self,
        sut: Scheduler[_SchedulerTestBaseContextCoT],
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        async with AsyncExecutor(sut):
            await sut.add(_Job("dependent", dependencies={"dependency"}))
            with pytest.raises(UnknownJobError):
                async with sut:
                    pass

    async def test_get__raises_when_cyclic(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        await sut.add(_Job("one", dependencies={"other"}))
        await sut.add(_Job("other", dependencies={"one"}))
        with pytest.raises(CyclicDependencyError):
            async with sut:
                await sut.get()

    async def test_get__raises_when_cancelled(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        await sut.cancel()
        with pytest.raises(Cancelled):
            await sut.get()

    async def test_get__raises_when_completed(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        await sut.complete()
        with pytest.raises(Completed):
            await sut.get()

    async def test_get___job_exception_should_cancel(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        reason = RuntimeError()

        class _Raise(Job[_SchedulerTestBaseContextCoT]):
            @override
            async def do(
                self, scheduler: Scheduler[_SchedulerTestBaseContextCoT], /
            ) -> None:
                raise reason

        await sut.add(_Raise(""))
        with pytest.raises(Cancelled) as exc_info:  # noqa PT012
            async with sut:
                batch = await sut.get()
                await batch()
        assert exc_info.value.__cause__ is reason

    async def test_get___done_when_cancelled(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.get` implementations.
        """
        await sut.add(_Job("one"))
        with pytest.raises(Cancelled) as exc_info:  # noqa PT012
            async with sut:
                batch = await sut.get()
                await sut.cancel()
                await batch()

        actual = [job.id for job in sut.context.jobs]
        assert actual == ["one"]

    async def test___aiter__(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.__aiter__` implementations.
        """
        completion = create_task(sut.complete())
        assert [batch async for batch in sut] == []
        await completion

    async def test_complete__when_completed(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.complete` implementations.
        """
        await sut.complete()
        await sut.complete()

    async def test_complete__when_cancelled(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.complete` implementations.
        """
        await sut.cancel()
        with pytest.raises(Cancelled):
            await sut.complete()

    async def test_cancel(self, sut: Scheduler[_SchedulerTestBaseContextCoT]) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.cancel` implementations.
        """
        await sut.add(Sleep(""))
        await sut.cancel()
        with pytest.raises(Cancelled):
            await sut.get()

    async def test_cancel__with_exception(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.cancel` implementations.
        """
        reason = RuntimeError()

        await sut.add(Sleep(""))
        await sut.cancel(reason)
        with pytest.raises(Cancelled) as exc_info:
            await sut.get()
        assert exc_info.value.__cause__ is reason

    async def test_cancel__when_cancelled(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.cancel` implementations.
        """
        await sut.cancel()
        await sut.cancel()

    async def test_cancel__when_completed(
        self, sut: Scheduler[_SchedulerTestBaseContextCoT]
    ) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.cancel` implementations.
        """
        await sut.complete()
        await sut.cancel()

    async def test_context(self, sut: Scheduler[_SchedulerTestBaseContextCoT]) -> None:
        """
        Tests :py:meth:`betty.job.scheduler.Scheduler.context` implementations.
        """
        assert sut.context is sut.context
