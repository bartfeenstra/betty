from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.job import Context, Job
from betty.progresses.no_op import NoOpProgress

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


class TestContext:
    def test_id(self) -> None:
        sut = Context()
        assert sut.id
        assert sut.id != Context().id

    def test_cache(self) -> None:
        sut = Context()
        sut.store  # noqa: B018

    def test_start(self) -> None:
        sut = Context()
        sut.start  # noqa: B018

    def test_progress(self) -> None:
        progress = NoOpProgress()
        sut = Context(progress=progress)
        assert sut.progress is progress

    def test_progress__default(self) -> None:
        sut = Context()
        sut.progress  # noqa: B018


class _Job(Job):
    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        pass


class TestJob:
    def test_id(self) -> None:
        job_id = "my-first-job"
        sut = _Job(job_id)
        assert sut.id == job_id

    def test_dependencies(self) -> None:
        dependencies = {"my-first-dependency", "my-second-dependency"}
        sut = _Job("my-first-job", dependencies=dependencies)
        assert sut.dependencies == dependencies

    def test_dependencies__default(self) -> None:
        sut = _Job("my-first-job")
        assert not sut.dependencies

    def test_dependents(self) -> None:
        dependents = {"my-first-dependent", "my-second-dependent"}
        sut = _Job("my-first-job", dependents=dependents)
        assert sut.dependents == dependents

    def test_dependents__default(self) -> None:
        sut = _Job("my-first-job")
        assert not sut.dependents

    def test_priority(self) -> None:
        sut = _Job("my-first-job", priority=True)
        assert sut.priority

    def test_priority__default(self) -> None:
        sut = _Job("my-first-job")
        assert not sut.priority
