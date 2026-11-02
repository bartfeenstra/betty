from __future__ import annotations

from betty.entities.note import Note
from betty.test_utils.entity.associations.has_notes import DummyHasNotes


class TestHasNotes:
    def test_notes(self) -> None:
        note = Note("-")
        sut = DummyHasNotes(notes=[note])
        assert list(sut.notes) == [note]
