"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import Plain, _
from betty.project.extension import ConfigurableExtension, ExtensionDefinition
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.extension.gramps.jobs import LoadAncestry
from betty.project.load import Loader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext


@final
@ExtensionDefinition(
    id="gramps",
    label=Plain("Gramps"),
    description=_("Load Gramps family trees."),
)
class Gramps(Loader, ConfigurableExtension[GrampsConfiguration]):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @override
    @classmethod
    def new_default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    @override
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(LoadAncestry())
