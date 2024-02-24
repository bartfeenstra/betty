from __future__ import annotations

from betty.job import Context


class TestContext:
    async def test_claim(self) -> None:
        sut = Context()
        job_ids = ('job ID 1', 'job ID 2', 'job ID 3')
        for job_id in job_ids:
            assert sut.claim(job_id)
            assert not sut.claim(job_id)
