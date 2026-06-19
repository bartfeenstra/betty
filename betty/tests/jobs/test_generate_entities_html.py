import pytest

from betty.entities.citation import Citation
from betty.entities.enclosure import Enclosure
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.entity import Entity
from betty.jobs.generate_entities_html import GenerateEntitiesHtml
from betty.privacy import Privacy
from betty.project import Project
from betty.roles.unknown import UnknownRole
from betty.test_utils.jinja import assert_betty_html
from betty.test_utils.job import do
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestGenerateEntitiesHtml:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="my-first-citation"),
            Event(id="my-first-event"),
            File(__file__, id="my-first-file"),
            Note(DUMMY_LOCALIZABLE, id="my-first-note"),
            Person(id="my-first-person"),
            Place(id="my-first-place"),
            Source(id="my-first-source"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_project: Project) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesHtml(project=isolated_project))

        await assert_betty_html(
            isolated_project, f"/{entity.plugin().id}/{entity.id}/index.html"
        )

    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source()),
            Citation(source=Source(), id="my-first-citation", privacy=Privacy.PRIVATE),
            Enclosure(enclosee=Place(), encloser=Place()),
            Event(),
            Event(id="my-first-event", privacy=Privacy.PRIVATE),
            File(__file__),
            File(__file__, id="my-first-file", privacy=Privacy.PRIVATE),
            Note(DUMMY_LOCALIZABLE),
            Note(DUMMY_LOCALIZABLE, id="my-first-note", privacy=Privacy.PRIVATE),
            Person(),
            Person(id="my-first-person", privacy=Privacy.PRIVATE),
            PersonName(individual="Jane", person=Person()),
            Presence(Person(), UnknownRole(), Event()),
            Place(),
            Place(id="my-first-place", privacy=Privacy.PRIVATE),
            Source(),
            Source(id="my-first-source", privacy=Privacy.PRIVATE),
        ],
    )
    async def test_do__with_non_publishable_entity(
        self, entity: Entity, isolated_project: Project
    ) -> None:
        isolated_project.ancestry.add(entity)
        await do(GenerateEntitiesHtml(project=isolated_project))

        assert not (
            isolated_project.www_directory
            / entity.plugin().id
            / entity.id
            / "index.html"
        ).exists()
