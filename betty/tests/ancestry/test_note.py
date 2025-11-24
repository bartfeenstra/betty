from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.ancestry.note import Note
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityDefinitionTestBase, EntityTestBase
from betty.tests.ancestry.test_has_notes import DummyHasNotes

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.model import Entity
    from betty.plugin import PluginDefinition
import pytest


class TestNoteDefinition(EntityDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Note.plugin


class TestNote(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Note("Betty wrote this.")

    async def test___init____with_entity(self) -> None:
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

    async def test_dump_linked_data__should_dump_full(self) -> None:
        note = Note("The Note", id="the_note")
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": False,
            "text": {DEFAULT_LOCALE: "The Note"},
            "entity": None,
            "links": [],
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
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
            "entity": None,
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected
