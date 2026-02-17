from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, override

import pytest

from betty.job import Context
from betty.job.executor.threading import ThreadPoolExecutor
from betty.test_utils.job.executor import ExecutorTestBase

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.job.executor import Executor
    from betty.job.scheduler import Scheduler

_ContextCoT = TypeVar("_ContextCoT", bound=Context, covariant=True)


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
    ) -> Callable[[Scheduler[Context]], Executor]:
        return lambda scheduler: ThreadPoolExecutor(
            scheduler,
            async_concurrency=request.param[0],
            threading_concurrency=request.param[1],
        )
