from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entities.note import Note
from betty.localizer import default_localizer
from betty.test_utils.entity import EntityTestBase
from betty.test_utils.entity.associations.has_notes import DummyHasNotes
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from betty.entity import Entity


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
        sut = Note("Betty wrote this.", id="my-first-note")
        assert sut.id == "my-first-note"

    def test_text(self) -> None:
        text = "Betty wrote this."
        sut = Note(text)
        assert sut.text.localize(default_localizer) == text

    def test_entity(self) -> None:
        entity = DummyHasNotes()
        sut = Note(DUMMY_LOCALIZABLE)
        sut.entity = entity
        assert sut.entity is entity
