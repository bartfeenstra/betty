from __future__ import annotations

from pathlib import Path
from typing import Sequence, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.test_utils.model import EntityTestBase
from betty.tests.ancestry.test___init__ import DummyHasFileReferences

if TYPE_CHECKING:
    from betty.model import Entity


class TestFileReference(EntityTestBase):
    @override
    def get_sut_class(self) -> type[FileReference]:
        return FileReference

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        referee = DummyHasFileReferences()
        file = File(Path())
        return [
            FileReference(referee, file),
            FileReference(referee, file, focus=(1, 2, 3, 4)),
        ]

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
