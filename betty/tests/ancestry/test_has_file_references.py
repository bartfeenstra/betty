from __future__ import annotations

from pathlib import Path

from betty.ancestry import FileReference
from betty.ancestry.file import File
from betty.tests.ancestry.test___init__ import DummyHasFileReferences


class TestHasFileReferences:
    async def test_file_references(self) -> None:
        sut = DummyHasFileReferences()
        assert list(sut.file_references) == []
        file_one = File(path=Path())
        file_two = File(path=Path())
        FileReference(sut, file_one)
        FileReference(sut, file_two)
        assert [file_reference.file for file_reference in sut.file_references] == [
            file_one,
            file_two,
        ]
