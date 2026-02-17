from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.job.executor.asyncio import AsyncExecutor
from betty.test_utils.job.executor import ExecutorTestBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.job.executor import Executor
    from betty.job.scheduler import Scheduler


class TestAsyncExecutor(ExecutorTestBase):
    @pytest.fixture(params=(1, 999))
    @override
    async def new_sut(
        self, request: pytest.FixtureRequest
    ) -> Callable[[Scheduler], Executor]:
        return lambda scheduler: AsyncExecutor(scheduler, concurrency=request.param)
