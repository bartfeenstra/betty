"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.job import Job
from betty.plugins.enricher.populate_links import PopulateLink
from betty.plugins.entity.link import Link

if TYPE_CHECKING:
    from betty.entity import Entity
    from betty.job.scheduler import Scheduler
    from betty.project import Project


class PopulateEntity(Job):
    """
    Populate an entity.
    """

    def __init__(self, entity: Entity, *, project: Project):
        super().__init__(
            self.id_for(entity),
            dependents={PopulateLink.id_for(entity)}
            if isinstance(entity, Link)
            else (),
        )
        self._project = project
        self._entity = entity

    @classmethod
    def id_for(cls, entity: Entity) -> str:
        """
        Get the job ID.
        """
        return f"wiki:populate:{entity.plugin().id}:{entity.id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        from betty.plugins.extension.wiki import Wiki

        wiki = await self._project.extensions[Wiki]
        populator = await wiki.populator
        await populator.populate(self._entity)
