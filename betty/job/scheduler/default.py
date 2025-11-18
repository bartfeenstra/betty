"""
Betty's default job scheduler.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from contextlib import asynccontextmanager
from graphlib import CycleError, TopologicalSorter
from typing import TYPE_CHECKING, Generic, TypeVar, cast, final

from typing_extensions import override

from betty.classtools import Singleton
from betty.concurrent import AsynchronizedLock, backoff
from betty.job import Context, Job
from betty.job.scheduler import (
    Cancelled,
    Completed,
    CyclicDependencyError,
    DuplicateJobError,
    Released,
    ScheduledJobBatch,
    Scheduler,
    UnknownJobError,
)
from betty.locale.localizable import Plain
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Callable,
        MutableMapping,
        MutableSequence,
        Sequence,
    )

    from betty.progress import Progress
    from betty.user import User


_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


class _ScheduledJobBatch:
    def __init__(
        self,
        scheduler: Scheduler[_ContextCoT],
        user: User,
        done: Callable[[Sequence[str]], Awaitable[None]],
        jobs: Sequence[Job[_ContextCoT]],
    ):
        self._scheduler = scheduler
        self._user = user
        self._done = done
        self._jobs = jobs

    async def __call__(self) -> None:
        try:
            for job in self._jobs:
                await self._user.message_debug(Plain(f'Doing job "{job.id}"...'))
                await job.do(self._scheduler)
        except BaseException as reason:
            await self._scheduler.cancel(reason)
            return
        await self._done([job.id for job in self._jobs])


@final
class _UnknownJob(Singleton):
    pass


@final
@threadsafe
class DefaultScheduler(Generic[_ContextCoT], Scheduler[_ContextCoT]):
    """
    Betty's default job scheduler.
    """

    def __init__(
        self,
        context: _ContextCoT,
        *,
        progress: Progress,
        user: User,
    ):
        self._context = context
        self._progress = progress
        self._user = user
        self._lock = AsynchronizedLock.new_threadsafe()
        self._released = False
        self._cancelled = False
        self._cancelled_reason: BaseException | None = None
        self._completed = False
        self._jobs: MutableMapping[str, Job[_ContextCoT] | _UnknownJob] = defaultdict(
            _UnknownJob
        )
        self._job_dependencies: MutableMapping[str, set[str]] = defaultdict(set)
        self._scheduled_jobs: set[str] = set()
        self._releasable_jobs_queue: MutableSequence[str] = []
        self._releasable_jobs_sorter: TopologicalSorter[str] | None = None
        self._released_jobs: set[str] = set()
        self._done_jobs: set[str] = set()

    @override
    @property
    def context(self) -> _ContextCoT:
        return self._context

    def _is_open(self) -> bool:
        return not self._cancelled and not self._completed

    def _assert_open(self) -> None:
        self._assert_not_cancelled()
        self._assert_not_completed()

    def _assert_not_cancelled(self) -> None:
        if self._cancelled:
            if isinstance(self._cancelled_reason, Cancelled):
                raise self._cancelled_reason
            raise Cancelled from self._cancelled_reason

    def _assert_not_completed(self) -> None:
        if self._completed:
            raise Completed

    @override
    async def add(self, *jobs: Job[_ContextCoT]) -> None:
        async with self._lock:
            self._assert_open()
            self._releasable_jobs_sorter = None
            for job in jobs:
                if not isinstance(self._jobs[job.id], _UnknownJob):
                    raise DuplicateJobError(job.id)
                if job.dependents:
                    if self._released:
                        raise Released
                    for dependent in job.dependents:
                        self._job_dependencies[dependent].add(job.id)
                self._jobs[job.id] = job
                self._scheduled_jobs.add(job.id)
                self._job_dependencies[job.id].update(
                    job.dependencies - self._done_jobs
                )
            await self._progress.add(len(jobs))

    @override
    async def release(self) -> None:
        async with self._lock:
            self._released = True

    def _update_releasable_jobs(self) -> None:
        if self._releasable_jobs_sorter is None:
            self._releasable_jobs_sorter = TopologicalSorter(self._job_dependencies)
            try:
                self._releasable_jobs_sorter.prepare()
            except CycleError as error:
                raise CyclicDependencyError(error.args[1]) from None

        possibly_newly_releasable_job_ids = self._releasable_jobs_sorter.get_ready()
        if possibly_newly_releasable_job_ids:
            newly_releasable_job_ids = set()
            unknown_job_id: str | None = None
            for possibly_newly_releasable_job_id in possibly_newly_releasable_job_ids:
                # A job may have been marked done since the last update.
                if possibly_newly_releasable_job_id in self._done_jobs:
                    self._releasable_jobs_sorter.done(possibly_newly_releasable_job_id)
                # Ignore jobs that have been issued already.
                elif possibly_newly_releasable_job_id in self._released_jobs:
                    continue
                else:
                    possibly_newly_releasable_job = self._jobs[
                        possibly_newly_releasable_job_id
                    ]
                    if isinstance(possibly_newly_releasable_job, _UnknownJob):
                        unknown_job_id = possibly_newly_releasable_job_id
                        continue
                    self._scheduled_jobs.discard(possibly_newly_releasable_job_id)
                    newly_releasable_job_ids.add(possibly_newly_releasable_job_id)
            self._releasable_jobs_queue = [
                job.id
                for job in sorted(
                    cast(
                        Iterable[Job[_ContextCoT]],
                        (
                            self._jobs[job_id]
                            for job_id in {
                                *self._releasable_jobs_queue,
                                *newly_releasable_job_ids,
                            }
                            if not isinstance(self._jobs[job_id], _UnknownJob)
                        ),
                    ),
                    key=lambda job: job.priority,
                    reverse=True,
                )
            ]
            if (
                not self._releasable_jobs_queue
                and not self._released_jobs
                and unknown_job_id is not None
            ):
                raise UnknownJobError(unknown_job_id)

    @override  # noqa RET503
    async def get(self) -> ScheduledJobBatch:  # type: ignore[return]
        async with self._cancel_on_exception():
            async for _ in backoff():
                async with self._lock:
                    batch = await self._get()
                    if batch is not None:
                        return batch

    async def _get(self) -> ScheduledJobBatch | None:
        self._assert_open()
        if not self._released:
            return None
        self._update_releasable_jobs()

        jobs: MutableSequence[Job[_ContextCoT]] = []
        index = 0
        releasable_job_count = len(self._releasable_jobs_queue)
        while len(jobs) <= 9 and index < releasable_job_count:
            releasable_job = self._jobs[self._releasable_jobs_queue[index]]
            assert isinstance(releasable_job, Job)
            if jobs and (jobs[0].priority or releasable_job.priority):
                break
            self._releasable_jobs_queue.pop(index)
            releasable_job_count -= 1
            self._released_jobs.add(releasable_job.id)
            jobs.append(releasable_job)
        if jobs:
            return _ScheduledJobBatch(self, self._user, self._done, jobs)
        return None

    async def _done(self, job_ids: Sequence[str]) -> None:
        async with self._cancel_on_exception():
            async with self._lock:
                for job_id in job_ids:
                    if self._releasable_jobs_sorter is not None:
                        self._releasable_jobs_sorter.done(job_id)
                    self._released_jobs.remove(job_id)
                    self._done_jobs.add(job_id)
                    self._job_dependencies.pop(job_id)
                    for job_dependencies in self._job_dependencies.values():
                        job_dependencies.discard(job_id)
            await self._progress.done(len(job_ids))

    @asynccontextmanager
    async def _cancel_on_exception(self) -> AsyncIterator[None]:
        try:
            yield
        except BaseException as exception:
            await self.cancel(exception)
            raise

    @override
    async def cancel(self, reason: BaseException | None = None) -> None:
        async with self._lock:
            if not self._is_open():
                return
            self._assert_open()
            self._cancelled = True
            self._cancelled_reason = reason

    @override
    async def complete(self) -> None:
        async with self._cancel_on_exception():
            async for _ in backoff():
                async with self._lock:
                    if self._completed:
                        return
                    self._assert_not_cancelled()
                    if (
                        not self._scheduled_jobs
                        and not self._releasable_jobs_queue
                        and not self._released_jobs
                    ):
                        self._completed = True
                        return
