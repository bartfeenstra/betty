"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import StaticTranslations, _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.extension.gramps.jobs import LoadAncestry
from betty.project.load import Loader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext


@final
class Gramps(ShorthandPluginBase, Loader, ConfigurableExtension[GrampsConfiguration]):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    _plugin_id = "gramps"
    _plugin_label = StaticTranslations("Gramps")
    _plugin_description = _(
        'Load <a href="https://gramps-project.org/">Gramps</a> family trees.'
    )

    @override
    @classmethod
    def new_default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    @override
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(LoadAncestry())
