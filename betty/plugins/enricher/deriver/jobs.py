"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.deriver import Deriver as DeriverApi
from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


class DeriveAncestry(Job):
    """
    Derive information for an ancestry.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "deriver:derive"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        deriver = DeriverApi(self._project)
        await deriver.derive()
