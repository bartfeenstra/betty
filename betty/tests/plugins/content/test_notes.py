from betty.document import Document
from betty.entities.note import Note
from betty.plugins.content.notes import Notes
from betty.project import Project
from betty.test_utils.ancestry.has_notes import DummyHasNotes


class TestNotes:
    async def test_build_template__without_has_notes_resource(
        self, isolated_project: Project
    ) -> None:
        sut = await Notes.new(isolated_project)
        assert await sut.build(document=Document()) is None

    async def test_build_template__without_notes(
        self, isolated_project: Project
    ) -> None:
        has_notes = DummyHasNotes()
        isolated_project.ancestry.add(has_notes)
        sut = await Notes.new(isolated_project)
        assert await sut.build(document=Document(has_notes)) is None

    async def test_build_template__with_notes(self, isolated_project: Project) -> None:
        note_text = "Hello, world!"
        has_notes = DummyHasNotes(notes=[Note(note_text)])
        isolated_project.ancestry.add(has_notes)
        sut = await Notes.new(isolated_project)
        actual = await sut.build(document=Document(has_notes))
        assert actual is not None
        assert note_text in actual
