"""
Jobs to generate artifacts for entity types.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.definition import ResolvableDefinition, resolve_definition
from betty.job import Job
from betty.jobs.generate_www_directory import GenerateWwwDirectory

if TYPE_CHECKING:
    from betty.entity import EntityDefinition
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateEntityType(Job):
    """
    Generate an entity type.
    """

    __slots__ = ("_entity_type", "_project")

    def __init__(
        self,
        entity_type: ResolvableDefinition[EntityDefinition],
        /,
        *,
        project: Project,
    ):
        super().__init__(
            self.id_for(entity_type), dependencies=[GenerateWwwDirectory.id_for]
        )
        self._entity_type = resolve_definition(entity_type)
        self._project = project

    @classmethod
    def id_for(cls, entity_type: ResolvableDefinition[EntityDefinition], /) -> str:
        """
        Get the job ID.
        """
        return f"generate-entity-type:{resolve_definition(entity_type).id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(
            *(
                to_thread(
                    (
                        self._project.localize_www_directory(locale.locale)
                        / Path(self._entity_type.id)
                    ).mkdir
                )
                for locale in self._project.locales
            )
        )
