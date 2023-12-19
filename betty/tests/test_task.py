from __future__ import annotations

from betty.task import Context


class TestBatch:
    async def test_claim(self) -> None:
        sut = Context()
        task_ids = ('task ID 1', 'task ID 2', 'task ID 3')
        for task_id in task_ids:
            assert sut.claim(task_id)
            assert not sut.claim(task_id)
