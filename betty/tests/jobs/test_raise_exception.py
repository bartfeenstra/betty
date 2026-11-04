import pytest

from betty.job.scheduler import Cancelled
from betty.jobs.raise_exception import RaiseException
from betty.test_utils.job import do


class TestRaiseException:
    async def test_do(self) -> None:
        reason = RuntimeError()
        with pytest.raises(Cancelled) as exc_info:
            await do(RaiseException("", reason))
        assert exc_info.value.__cause__ is reason
