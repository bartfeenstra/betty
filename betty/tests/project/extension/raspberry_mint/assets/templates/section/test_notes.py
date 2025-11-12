from betty.ancestry.note import Note
from betty.locale.localizable import Plain
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.resource import new_context
from betty.test_utils.jinja2 import assert_template_file
from betty.tests.ancestry.test_has_notes import DummyHasNotes


async def test_minimal() -> None:
    has_notes = DummyHasNotes()
    async with assert_template_file(
        data={
            "resource": new_context(has_notes),
        },
        extensions={RaspberryMint},
        template="section/notes.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_public_notes() -> None:
    note_text = "Hello, world!"
    has_notes = DummyHasNotes(notes=[Note(Plain(note_text))])
    async with assert_template_file(
        data={
            "resource": new_context(has_notes),
        },
        extensions={RaspberryMint},
        template="section/notes.html.j2",
    ) as (actual, _):
        assert note_text in actual


async def test_without_public_notes() -> None:
    note_text = "Hello, world!"
    has_notes = DummyHasNotes(notes=[Note(Plain(note_text), private=True)])
    async with assert_template_file(
        data={
            "resource": new_context(has_notes),
        },
        extensions={RaspberryMint},
        template="section/notes.html.j2",
    ) as (actual, _):
        assert not actual
