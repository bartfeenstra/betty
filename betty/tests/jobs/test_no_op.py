from betty.jobs.no_op import NoOpJob
from betty.test_utils.job import do


class TestNoOpJob:
    async def test_do(self) -> None:
        await do(NoOpJob(""))
