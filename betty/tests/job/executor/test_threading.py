from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.job.executor.threading import ThreadPoolExecutor
from betty.test_utils.job.executor import ExecutorTestBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.job.executor import Executor
    from betty.job.scheduler import Scheduler


class TestThreadPoolExecutor(ExecutorTestBase):
    @pytest.fixture(
        params=(
            (1, 1),
            (1, 9),
            (9, 1),
            (9, 9),
        )
    )
    @override
    async def new_sut(
        self, request: pytest.FixtureRequest
    ) -> Callable[[Scheduler], Executor]:
        return lambda scheduler: ThreadPoolExecutor(
            scheduler,
            async_concurrency=request.param[0],
            threading_concurrency=request.param[1],
        )
