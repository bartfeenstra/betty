from __future__ import annotations

from pathlib import Path

from betty.associations.to_one import Placeholder
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.test_utils.entity.associations.has_file_references import (
    DummyHasFileReferences,
)


class TestHasFileReferences:
    def test_files(self) -> None:
        file_one = File(path=Path())
        file_two = File(path=Path())
        file_reference_1 = FileReference(Placeholder, file_one)
        file_reference_2 = FileReference(Placeholder, file_two)
        sut = DummyHasFileReferences(files=[file_reference_1, file_reference_2])
        assert list(sut.files) == [file_reference_1, file_reference_2]
        assert file_reference_1.referee is sut
        assert file_reference_2.referee is sut
