"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.config import Configurable
from betty.locale.localizable import Plain, _
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.extension.gramps.jobs import LoadAncestry
from betty.project.load import Loader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext


@final
@ExtensionDefinition(
    id="gramps",
    label=Plain("Gramps"),
    description=_("Load Gramps family trees."),
)
class Gramps(Loader, Configurable[GrampsConfiguration], Extension):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project, configuration=GrampsConfiguration())

    @override
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(LoadAncestry())
