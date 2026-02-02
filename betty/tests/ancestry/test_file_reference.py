from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity


class TestFileReference(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return FileReference(DummyHasFileReferences(), File(Path()))

    def test_focus(self) -> None:
        sut = FileReference(DummyHasFileReferences(), File(Path()))
        focus = (1, 2, 3, 4)
        sut.focus = focus
        assert sut.focus == focus

    def test_file(self) -> None:
        file = File(Path())
        sut = FileReference(DummyHasFileReferences(), file)
        assert sut.file is file

    def test_referee(self) -> None:
        referee = DummyHasFileReferences()
        sut = FileReference(referee, File(Path()))
        assert sut.referee is referee
