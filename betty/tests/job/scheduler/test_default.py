from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.job import Context
from betty.job.scheduler.default import DefaultScheduler
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.test_utils.job import NoOpJob
from betty.test_utils.job.scheduler import SchedulerTestBase, SchedulerTestBaseContext
from betty.user.no_op import NoOpUser

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


class _Progress(Progress):
    def __init__(self):
        self.total = 0

    @override
    async def add(self, add: int = 1, /) -> None:
        self.total += add

    @override
    async def done(self, done: int = 1, /) -> None:
        self.total -= done


class TestDefaultScheduler(SchedulerTestBase[SchedulerTestBaseContext]):
    @pytest.fixture
    @override
    def sut(self) -> Scheduler[SchedulerTestBaseContext]:
        return DefaultScheduler(
            SchedulerTestBaseContext(), progress=NoOpProgress(), user=NoOpUser()
        )

    async def test_progress(self) -> None:
        progress = _Progress()
        async with DefaultScheduler(
            Context(), progress=progress, user=NoOpUser()
        ) as sut:
            await sut.add(NoOpJob("job"))
            assert progress.total == 1
            batch = await sut.get()
            await batch()
            assert progress.total == 0
