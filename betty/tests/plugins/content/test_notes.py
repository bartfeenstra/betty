from betty.app import App
from betty.document import Document
from betty.plugins.content.notes import Notes
from betty.plugins.entity.note import Note
from betty.project import Project
from betty.test_utils.ancestry.has_notes import DummyHasNotes


class TestNotes:
    async def test_build_template__without_has_notes_resource(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Notes.new(project)
            assert await sut.build(document=Document()) is None

    async def test_build_template__without_notes(self, isolated_app: App) -> None:
        has_notes = DummyHasNotes()
        async with Project.new_isolated(isolated_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new(project)
            assert await sut.build(document=Document(has_notes)) is None

    async def test_build_template__with_notes(self, isolated_app: App) -> None:
        note_text = "Hello, world!"
        has_notes = DummyHasNotes(notes=[Note(note_text)])
        async with Project.new_isolated(isolated_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new(project)
            actual = await sut.build(document=Document(has_notes))
            assert actual is not None
            assert note_text in actual
