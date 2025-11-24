"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.config.factory import ConfigurationDependentSelfFactory
from betty.locale.localizable import _
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.extension.gramps.jobs import LoadAncestry
from betty.project.load import Loader
from betty.typing import private

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext
    from betty.service.level.factory import AnyFactoryTarget


@final
@ExtensionDefinition(
    id="gramps",
    label="Gramps",
    description=_("Load Gramps family trees."),
)
class Gramps(Loader, ConfigurationDependentSelfFactory[GrampsConfiguration], Extension):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @private
    def __init__(self, *, configuration: GrampsConfiguration | None = None):
        super().__init__(
            configuration=GrampsConfiguration()
            if configuration is None
            else configuration
        )

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: GrampsConfiguration
    ) -> AnyFactoryTarget[Self]:
        return lambda: cls(configuration=configuration)

    @override
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(LoadAncestry())
