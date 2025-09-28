"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry import event_type
from betty.ancestry.event_type.event_types import DerivableEventType
from betty.deriver import Deriver as DeriverApi
from betty.job import Job
from betty.project import ProjectContext

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


class DeriveAncestry(Job[ProjectContext]):
    """
    Derive information for an ancestry.
    """

    def __init__(self):
        super().__init__(self.id_for())

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "deriver:derive"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project

        deriver = DeriverApi(
            project.ancestry,
            project.configuration.lifetime_threshold,
            project.event_type_repository,
            {
                plugin
                async for plugin in event_type.EVENT_TYPE_REPOSITORY
                if issubclass(plugin, DerivableEventType)
            },
            user=project.app.user,
        )
        await deriver.derive()
