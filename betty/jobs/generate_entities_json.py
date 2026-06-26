"""
Jobs to generate JSON resources for entities.
"""

from __future__ import annotations

from asyncio import gather
from json import dumps
from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.job import Job
from betty.jobs import _create_json_resource

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateEntitiesJson(Job):
    """
    Generate JSON resources for entities.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for(), priority=True)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-entities-json"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(*[
            scheduler.add(_GenerateEntityJson(self._project, entity_type, entity.id))
            async for entity_type in self._project.plugins[EntityDefinition]
            for entity in self._project.ancestry[entity_type.cls]
        ])


@final
class _GenerateEntityJson(Job):
    def __init__(
        self, project: Project, entity_type: EntityDefinition, entity_id: str, /
    ):
        super().__init__(self.id_for(entity_type, entity_id))
        self._project = project
        self._entity_type = entity_type
        self._entity_id = entity_id

    @classmethod
    def id_for(cls, entity_type: EntityDefinition, entity_id: str) -> str:
        return f"generate-entity-json:{entity_type.id}:{entity_id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        entity = self._project.ancestry[self._entity_type.cls][self._entity_id]
        entity_path = self._project.www_directory / self._entity_type.id / entity.id
        await _create_json_resource(
            entity_path,
            dumps(await entity.data().linked_data_porter.dump(self._project, entity)),
        )
