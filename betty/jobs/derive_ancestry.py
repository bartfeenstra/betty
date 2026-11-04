"""
Ancestry derivation jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final, override

from betty.deriver import Deriver as DeriverApi
from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class DeriveAncestry(Job):
    """
    Derive information for an ancestry.
    """

    id_for: Final[str] = "deriver:derive"
    """
    The job ID.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for)
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        deriver = DeriverApi(self._project)
        await deriver.derive()
