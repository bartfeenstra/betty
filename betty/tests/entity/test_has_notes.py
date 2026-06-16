from __future__ import annotations

from betty.entities.note import Note
from betty.test_utils.ancestry.has_notes import DummyHasNotes
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestHasNotes:
    def test_notes(self) -> None:
        note = Note(DUMMY_LOCALIZABLE)
        sut = DummyHasNotes(notes=[note])
        assert list(sut.notes) == [note]
