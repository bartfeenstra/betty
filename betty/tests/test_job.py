from __future__ import annotations

from betty.job import Context
from betty.progress.no_op import NoOpProgress


class TestContext:
    def test_id(self) -> None:
        sut = Context()
        assert sut.id
        assert sut.id != Context().id

    def test_cache(self) -> None:
        sut = Context()
        sut.cache  # noqa B018

    def test_start(self) -> None:
        sut = Context()
        sut.start  # noqa B018

    def test_progress__with___init___arg(self) -> None:
        progress = NoOpProgress()
        sut = Context(progress=progress)
        assert sut.progress is progress

    def test_progress__without___init___arg(self) -> None:
        sut = Context()
        sut.progress  # noqa B018
