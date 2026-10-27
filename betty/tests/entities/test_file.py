from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, cast, override

import pytest

from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entities.note import Note
from betty.entity import Entity
from betty.localizer import default_localizer
from betty.media_types.plain_text import PLAIN_TEXT
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase
from betty.test_utils.entity.associations.has_file_references import (
    DummyHasFileReferences,
)
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestFile(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            File(__file__),
            File(__file__, description="My First File"),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test_id(self) -> None:
        sut = File(Path(__file__), id="my-first-file")
        assert sut.id == "my-first-file"

    def test_name__with_name(self, tmp_path: Path) -> None:
        name = "a-file.a-suffix"
        sut = File(
            tmp_path / "file",
            name=name,
        )
        assert sut.name == name

    def test_private(self) -> None:
        sut = File(Path(__file__))
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    def test_media_type(self) -> None:
        sut = File(Path(__file__))
        assert sut.media_type is None
        media_type = PLAIN_TEXT
        sut.media_type = media_type
        assert sut.media_type == media_type

    def test_path__with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_path = Path(f.name)
            sut = File(
                id="my-first-file",
                path=file_path,
            )
            assert sut.path == file_path

    def test_path__with_str(self) -> None:
        with NamedTemporaryFile() as f:
            sut = File(
                id="my-first-file",
                path=Path(f.name),
            )
            assert sut.path == Path(f.name)

    def test_description(self) -> None:
        sut = File(Path(__file__))
        assert not sut.description
        description = "Hi, my name is Betty!"
        sut.description = description
        assert sut.description is not None
        assert sut.description.localize(default_localizer) == description

    def test_notes(self) -> None:
        sut = File(Path(__file__))
        assert list(sut.notes) == []
        notes = [Note(DUMMY_LOCALIZABLE), Note(DUMMY_LOCALIZABLE)]
        sut.notes = notes
        assert list(sut.notes) == notes

    def test_referees(self) -> None:
        sut = File(Path(__file__))
        assert list(sut.referees) == []

        entity_one = DummyHasFileReferences()
        entity_two = DummyHasFileReferences()
        FileReference(entity_one, sut)
        FileReference(entity_two, sut)
        assert [file_reference.referee for file_reference in sut.referees] == [
            entity_one,
            entity_two,
        ]

    def test_citations(self) -> None:
        sut = File(Path(__file__))
        assert list(sut.citations) == []
