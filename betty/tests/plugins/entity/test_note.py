from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.entity.note import Note
from betty.privacy import Privacy
from betty.test_utils.ancestry.has_notes import DummyHasNotes
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.model import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.model import Entity
import pytest


class TestNote(EntityTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Entity:
        return Note("Betty wrote this.")

    def test___init____with_entity(self) -> None:
        entity = DummyHasNotes()
        sut = Note("Betty wrote this.", entity=entity)
        assert sut.entity is entity

    def test_id(self) -> None:
        note_id = "N1"
        sut = Note("Betty wrote this.", id=note_id)
        assert sut.id == note_id

    def test_text(self) -> None:
        text = "Betty wrote this."
        sut = Note(text)
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    def test_entity(self) -> None:
        entity = DummyHasNotes()
        sut = Note(DUMMY_LOCALIZABLE)
        sut.entity = entity
        assert sut.entity is entity

    async def test_dump_linked_data__should_dump_full(self) -> None:
        note = Note("The Note", id="the_note")
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": False,
            "text": {DEFAULT_LOCALE_TAG: "The Note"},
            "entity": None,
            "links": [],
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
        note = Note(
            "The Note",
            id="the_note",
            privacy=Privacy.PRIVATE,
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
