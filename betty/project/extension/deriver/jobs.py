"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

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
        deriver = DeriverApi(scheduler.context.project)
        await deriver.derive()
