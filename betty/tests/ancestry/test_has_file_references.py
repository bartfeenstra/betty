from __future__ import annotations

from pathlib import Path

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.model.association import TemporaryToOneResolver
from betty.tests.ancestry.test___init__ import DummyHasFileReferences


class TestHasFileReferences:
    async def test___init___with_file_references(self) -> None:
        file_one = File(path=Path())
        file_two = File(path=Path())
        file_reference_1 = FileReference(TemporaryToOneResolver(), file_one)
        file_reference_2 = FileReference(TemporaryToOneResolver(), file_two)
        sut = DummyHasFileReferences(
            file_references=[file_reference_1, file_reference_2]
        )
        assert list(sut.file_references) == [file_reference_1, file_reference_2]
        assert file_reference_1.referee is sut
        assert file_reference_2.referee is sut

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
