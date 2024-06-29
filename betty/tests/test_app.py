from __future__ import annotations

from betty.app import App


class TestApp:
    async def test_fetcher(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.fetcher is not None
