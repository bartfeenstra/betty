"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.enrichers.populate_links.jobs import PopulateLink
from betty.entities.link import Link
from betty.factory import Manufacturable
from betty.load import Enricher, EnricherDefinition
from betty.project import Project

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@EnricherDefinition("populate-links", label="Populate links", auto=True)
class PopulateLinks(Enricher, Manufacturable):
    """
    .. plugin:: enricher:populate-links.
    """

    def __init__(self, project: Project, /):
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project)

    @override
    async def enrich(self, scheduler: Scheduler, /) -> None:
        http_client, localizers = await gather(
            self._project.upstream.http_client, self._project.public_localizers
        )
        await scheduler.add(
            *(
                PopulateLink(link, http_client=http_client, localizers=localizers)
                for link in self._project.ancestry[Link]
            ),
        )
