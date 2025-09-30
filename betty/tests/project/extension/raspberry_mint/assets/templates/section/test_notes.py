from betty.ancestry.note import Note
from betty.locale.localizable import Plain
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file
from betty.tests.ancestry.test_has_notes import DummyHasNotes


async def test_minimal() -> None:
    entity = DummyHasNotes()
    async with assert_template_file(
        data={
            "entity": entity,
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/notes.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_public_notes() -> None:
    note_text = "Hello, world!"
    entity = DummyHasNotes(notes=[Note(Plain(note_text))])
    async with assert_template_file(
        data={
            "entity": entity,
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/notes.html.j2",
    ) as (actual, _):
        assert note_text in actual


async def test_without_public_notes() -> None:
    note_text = "Hello, world!"
    entity = DummyHasNotes(notes=[Note(Plain(note_text), private=True)])
    async with assert_template_file(
        data={
            "entity": entity,
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/notes.html.j2",
    ) as (actual, _):
        assert not actual
