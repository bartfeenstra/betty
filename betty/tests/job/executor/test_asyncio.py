from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, override

import pytest

from betty.job import Context
from betty.job.executor.asyncio import AsyncExecutor
from betty.test_utils.job.executor import ExecutorTestBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.job.executor import Executor
    from betty.job.scheduler import Scheduler

_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


class TestAsyncExecutor(ExecutorTestBase):
    @pytest.fixture(params=(1, 999))
    @override
    async def new_sut(
        self, request: pytest.FixtureRequest
    ) -> Callable[[Scheduler[Context]], Executor]:
        return lambda scheduler: AsyncExecutor(scheduler, concurrency=request.param)
