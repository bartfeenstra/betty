from betty.jobs.sleep import Sleep
from betty.test_utils.job import do


class TestSleep:
    async def test_do(self) -> None:
        await do(Sleep("", 0))
