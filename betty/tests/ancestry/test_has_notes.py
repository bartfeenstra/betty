from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry.has_notes import HasNotes
from betty.ancestry.note import Note
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump


class DummyHasNotes(HasNotes, DummyEntity):
    pass


class TestHasNotes:
    async def test_notes(self) -> None:
        sut = DummyHasNotes()
        assert list(sut.notes) == []

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "id": "my-first-has-notes",
                    "notes": [],
                },
                DummyHasNotes(id="my-first-has-notes"),
            ),
            (
                {
                    "id": "my-first-has-notes",
                    "notes": [],
                },
                DummyHasNotes(
                    notes=[Note(text="Hello, world!")], id="my-first-has-notes"
                ),
            ),
            (
                {
                    "id": "my-first-has-notes",
                    "notes": ["/note/my-first-note/index.json"],
                },
                DummyHasNotes(
                    notes=[Note(text="Hello, world!", id="my-first-note")],
                    id="my-first-has-notes",
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasNotes
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
