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
from betty.jobs.generate_entity_types_json import GenerateEntityTypesJson
from betty.project import Project
from betty.string import kebab_case_to_lower_camel_case
from betty.test_utils.jinja import assert_betty_json
from betty.test_utils.job import do


class TestGenerateEntityTypesJson:
    @pytest.mark.parametrize(
        "entity_type",
        [
            Citation,
            Enclosure,
            Event,
            File,
            Note,
            Person,
            PersonName,
            Presence,
            Place,
            Source,
        ],
    )
    async def test_do(
        self, entity_type: type[Entity], isolated_project: Project
    ) -> None:
        await do(GenerateEntityTypesJson(project=isolated_project))

        await assert_betty_json(
            isolated_project,
            f"/{entity_type.plugin().id}/index.json",
            f"{kebab_case_to_lower_camel_case(entity_type.plugin().id)}EntityCollectionResponse",
        )
