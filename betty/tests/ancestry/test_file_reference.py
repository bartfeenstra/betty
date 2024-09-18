from __future__ import annotations

from pathlib import Path

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.tests.ancestry.test___init__ import DummyHasFileReferences


class TestFileReference:
    async def test_focus(self) -> None:
        sut = FileReference(DummyHasFileReferences(), File(Path()))
        focus = (1, 2, 3, 4)
        sut.focus = focus
        assert sut.focus == focus

    async def test_file(self) -> None:
        file = File(Path())
        sut = FileReference(DummyHasFileReferences(), file)
        assert sut.file is file

    async def test_referee(self) -> None:
        referee = DummyHasFileReferences()
        sut = FileReference(referee, File(Path()))
        assert sut.referee is referee
