"""
Jobs to generate artifacts for entities.
"""

from __future__ import annotations

from asyncio import to_thread
from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.job import Job
from betty.jobs.generate_entity_type import GenerateEntityType

if TYPE_CHECKING:
    from betty.entity import Entity
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateEntity(Job):
    """
    Generate an entity.
    """

    __slots__ = ("_entity", "_project")

    def __init__(self, entity: Entity, /, *, project: Project):
        super().__init__(
            self.id_for(entity),
            dependencies=[GenerateEntityType.id_for(entity.definition)],
        )
        self._entity = entity
        self._project = project

    @classmethod
    def id_for(cls, entity: Entity, /) -> str:
        """
        Get the job ID.
        """
        return f"generate-entity:{entity.definition.id}:{entity.id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        for locale in self._project.locales:
            await to_thread(
                (
                    self._project.localize_www_directory(locale.locale)
                    / Path(self._entity.definition.id)
                    / self._entity.id
                ).mkdir
            )
