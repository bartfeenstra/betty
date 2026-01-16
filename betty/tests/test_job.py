from __future__ import annotations

from typing import TYPE_CHECKING

from betty.job import Context

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager


class TestContext:
    def test_id(self, multiprocessing_manager: SyncManager) -> None:
        sut = Context(manager=multiprocessing_manager)
        assert sut.id
        assert sut.id != Context(manager=multiprocessing_manager).id

    def test_cache(self, multiprocessing_manager: SyncManager) -> None:
        sut = Context(manager=multiprocessing_manager)
        sut.cache  # noqa: B018

    def test_start(self, multiprocessing_manager: SyncManager) -> None:
        sut = Context(manager=multiprocessing_manager)
        sut.start  # noqa: B018
