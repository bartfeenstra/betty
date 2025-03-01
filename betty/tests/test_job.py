from __future__ import annotations


from betty.job import Context
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager


class TestContext:
    async def test_cache(self, multiprocessing_manager: SyncManager) -> None:
        sut = Context(manager=multiprocessing_manager)
        sut.cache  # noqa B018

    async def test_start(self, multiprocessing_manager: SyncManager) -> None:
        sut = Context(manager=multiprocessing_manager)
        sut.start  # noqa B018
