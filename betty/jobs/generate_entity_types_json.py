"""
Jobs to generate JSON resources for entity types.
"""

from __future__ import annotations

from asyncio import gather
from json import dumps
from typing import TYPE_CHECKING, cast, final, override

from betty.entity import EntityDefinition
from betty.job import Job
from betty.jobs import _create_json_resource
from betty.json_schemas.project import project_schema_def_url
from betty.media_types.json import JSON
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.job.scheduler import Scheduler
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class GenerateEntityTypesJson(Job):
    """
    Generate JSON resources for entity types.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entity-types-json"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(*[
            scheduler.add(_GenerateEntityTypeJson(self._project, entity_type))
            async for entity_type in self._project.plugins[EntityDefinition]
        ])


@final
class _GenerateEntityTypeJson(Job):
    def __init__(self, project: Project, entity_type: EntityDefinition):
        super().__init__(self.id_for(entity_type))
        self._project = project
        self._entity_type = entity_type

    @classmethod
    def id_for(cls, entity_type: EntityDefinition) -> str:
        return f"generate-entity-type-json:{entity_type.id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        url_generator = await self._project.url_generator
        entity_type_directory = self._project.www_directory / self._entity_type.id
        data: PortableMapping = {
            "$schema": await project_schema_def_url(
                self._project,
                f"{kebab_case_to_lower_camel_case(self._entity_type.id)}EntityCollectionResponse",
            ),
            "collection": [],
        }
        for entity in self._project.ancestry[self._entity_type.cls]:
            cast("MutableSequence[str]", data["collection"]).append(
                url_generator.generate(
                    entity,
                    media_type=JSON,
                    absolute=True,
                )
            )
        await _create_json_resource(entity_type_directory, dumps(data))
