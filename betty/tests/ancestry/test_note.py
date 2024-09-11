from __future__ import annotations

from typing import Sequence, Mapping, Any, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.note import Note
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase
from betty.tests.ancestry.test_has_notes import DummyHasNotes

if TYPE_CHECKING:
    from betty.model import Entity


class TestNote(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Note]:
        return Note

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Note("My First Note"),
        ]

    async def test_id(self) -> None:
        note_id = "N1"
        sut = Note(
            id=note_id,
            text="Betty wrote this.",
        )
        assert sut.id == note_id

    async def test_text(self) -> None:
        text = "Betty wrote this."
        sut = Note(
            id="N1",
            text=text,
        )
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    async def test_entity(self) -> None:
        entity = DummyHasNotes()
        sut = Note(id="N1", text="")
        sut.entity = entity
        assert sut.entity is entity

    async def test_dump_linked_data_should_dump_full(self) -> None:
        note = Note(id="the_note", text="The Note")
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": False,
            "text": {"translations": {"und": "The Note"}},
            "entity": None,
            "links": [],
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        note = Note(
            id="the_note",
            text="The Note",
            private=True,
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": True,
            "links": [],
            "text": None,
            "entity": None,
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected
