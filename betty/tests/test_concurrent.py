import time

import pytest

from betty.asyncio import gather
from betty.concurrent import RateLimiter


class TestRateLimiter:
    @pytest.mark.parametrize('expected, iterations', [
        (0, 100),
        # This is one higher than the rate limiter's maximum, to ensure we spend at least one full period.
        (1, 101),
    ])
    async def test(self, expected: int, iterations: int) -> None:
        sut = RateLimiter(100)

        async def _task() -> None:
            async with sut:
                pass
        start = time.time()
        await gather(*(
            _task()
            for _
            in range(0, iterations)
        ))
        end = time.time()
        duration = end - start
        assert expected == round(duration)
