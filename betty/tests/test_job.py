from __future__ import annotations

from betty.job import Context


class TestContext:
    async def test_cache(self) -> None:
        sut = Context()
        sut.cache  # noqa B018

    async def test_start(self) -> None:
        sut = Context()
        sut.start  # noqa B018
