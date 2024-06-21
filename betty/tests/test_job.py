from __future__ import annotations

from betty.job import Context


class TestContext:
    async def test_start(self) -> None:
        sut = Context()
        sut.start  # noqa B018
