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
            Note("Betty wrote this."),
        ]

    async def test___init___with_entity(self) -> None:
        entity = DummyHasNotes()
        sut = Note("Betty wrote this.", entity=entity)
        assert sut.entity is entity

    async def test_id(self) -> None:
        note_id = "N1"
        sut = Note("Betty wrote this.", id=note_id)
        assert sut.id == note_id

    async def test_text(self) -> None:
        text = "Betty wrote this."
        sut = Note(text)
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    async def test_entity(self) -> None:
        entity = DummyHasNotes()
        sut = Note("")
        sut.entity = entity
        assert sut.entity is entity

    async def test_dump_linked_data_should_dump_full(self) -> None:
        note = Note("The Note", id="the_note")
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": False,
            "text": {"und": "The Note"},
            "entity": None,
            "links": [],
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        note = Note(
            "The Note",
            id="the_note",
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
