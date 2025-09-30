"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.link import Link
from betty.job import Job
from betty.project import ProjectContext
from betty.project.load.jobs import PopulateLink

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.model import Entity


class PopulateEntity(Job[ProjectContext]):
    """
    Populate an entity.
    """

    def __init__(self, entity: Entity):
        super().__init__(
            self.id_for(entity),
            dependents={PopulateLink.id_for(entity)}
            if isinstance(entity, Link)
            else None,
        )
        self._entity = entity

    @classmethod
    def id_for(cls, entity: Entity) -> str:
        """
        Get the job ID.
        """
        return f"wiki:populate:{entity.plugin.id}:{entity.id}"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        from betty.project.extension.wiki import Wiki

        project = scheduler.context.project
        extensions = await project.extensions
        populator = await extensions[Wiki].populator
        await populator.populate(self._entity)
