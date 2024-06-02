from __future__ import annotations

import pytest

from betty.job import Context
from betty.warnings import BettyDeprecationWarning


class TestContext:
    async def test_claim(self) -> None:
        sut = Context()
        job_ids = ("job ID 1", "job ID 2", "job ID 3")
        for job_id in job_ids:
            with pytest.warns(BettyDeprecationWarning):
                assert sut.claim(job_id)
                assert not sut.claim(job_id)

    async def test_start(self) -> None:
        sut = Context()
        sut.start  # noqa B018
