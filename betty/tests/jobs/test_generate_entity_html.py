import pytest

from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.entity import Entity
from betty.jobs.generate_entity import GenerateEntity
from betty.jobs.generate_entity_html import GenerateEntityHtml
from betty.jobs.generate_entity_type import GenerateEntityType
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.project import Project
from betty.test_utils.jinja import assert_betty_html
from betty.test_utils.job import do


class TestGenerateEntityHtml:
    @pytest.mark.parametrize(
        "entity",
        [
            Citation(source=Source(), id="my-first-citation"),
            Event(id="my-first-event"),
            File(__file__, id="my-first-file"),
            Note("-", id="my-first-note"),
            Person(id="my-first-person"),
            Place(id="my-first-place"),
            Source(id="my-first-source"),
        ],
    )
    async def test_do(self, entity: Entity, isolated_project: Project) -> None:
        await do(
            GenerateWwwDirectory(project=isolated_project),
            GenerateEntityType(entity.definition, project=isolated_project),
            GenerateEntity(entity, project=isolated_project),
            GenerateEntityHtml(entity, project=isolated_project),
        )
        await assert_betty_html(
            isolated_project, f"/{entity.definition.id}/{entity.id}/index.html"
        )
