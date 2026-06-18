import pytest

from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.entity import Entity
from betty.jobs.generate_entities_json import GenerateEntitiesJson
from betty.project import Project
from betty.string import kebab_case_to_lower_camel_case
from betty.test_utils.jinja import assert_betty_json
from betty.test_utils.job import do
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestGenerateEntitiesJson:
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
        await do(GenerateEntitiesJson(project=isolated_project))

        await assert_betty_json(
            isolated_project,
            f"/{entity.plugin().id}/{entity.id}/index.json",
            f"{kebab_case_to_lower_camel_case(entity.plugin().id)}Entity",
        )
