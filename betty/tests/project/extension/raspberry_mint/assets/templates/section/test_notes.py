from betty.ancestry.note import Note
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase
from betty.tests.ancestry.test_has_notes import DummyHasNotes


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "section/notes.html.j2"

    async def test_minimal(self) -> None:
        entity = DummyHasNotes()
        async with self.assert_template_file(
            data={
                "entity": entity,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert not actual

    async def test_with_public_notes(self) -> None:
        note_text = "Hello, world!"
        entity = DummyHasNotes(notes=[Note(note_text)])
        async with self.assert_template_file(
            data={
                "entity": entity,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert note_text in actual

    async def test_without_public_notes(self) -> None:
        note_text = "Hello, world!"
        entity = DummyHasNotes(notes=[Note(note_text, private=True)])
        async with self.assert_template_file(
            data={
                "entity": entity,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert not actual
