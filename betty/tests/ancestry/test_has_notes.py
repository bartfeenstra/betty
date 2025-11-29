from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry.has_notes import HasNotes
from betty.ancestry.note import Note
from betty.model import EntityPlugin
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping


@EntityPlugin(
    "dummy-has-notes",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasNotes(HasNotes):
    pass


class TestHasNotes:
    async def test___init___with_notes(self) -> None:
        note = Note(DUMMY_LOCALIZABLE)
        sut = DummyHasNotes(notes=[note])
        assert list(sut.notes) == [note]

    async def test_notes(self) -> None:
        sut = DummyHasNotes()
        assert list(sut.notes) == []
        note = Note(DUMMY_LOCALIZABLE)
        sut.notes = [note]
        assert list(sut.notes) == [note]

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@id": "https://example.com/dummy-has-notes/my-first-has-notes/index.json",
                    "id": "my-first-has-notes",
                    "notes": [],
                },
                DummyHasNotes(id="my-first-has-notes"),
            ),
            (
                {
                    "@id": "https://example.com/dummy-has-notes/my-first-has-notes/index.json",
                    "id": "my-first-has-notes",
                    "notes": [],
                },
                DummyHasNotes(notes=[Note("Hello, world!")], id="my-first-has-notes"),
            ),
            (
                {
                    "@id": "https://example.com/dummy-has-notes/my-first-has-notes/index.json",
                    "id": "my-first-has-notes",
                    "notes": ["/note/my-first-note/index.json"],
                },
                DummyHasNotes(
                    notes=[Note("Hello, world!", id="my-first-note")],
                    id="my-first-has-notes",
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasNotes
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
