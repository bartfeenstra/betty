"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.plugin import PluginIdentifier, ShorthandPluginBase
from betty.project.extension import Extension
from betty.project.extension.deriver import Deriver
from betty.project.extension.deriver.jobs import DeriveAncestry
from betty.project.extension.privatizer.jobs import PrivatizeAncestry
from betty.project.load import PostLoader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext


@final
class Privatizer(ShorthandPluginBase, PostLoader, Extension):
    """
    Extend the Betty Application with privatization features.
    """

    _plugin_id = "privatizer"
    _plugin_label = _("Privatizer")
    _plugin_description = _(
        "Determine if people can be proven to have died. If not, mark them and their associated entities private."
    )

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        return {Deriver}

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(
            PrivatizeAncestry(
                dependencies={DeriveAncestry.id_for()}
                if Deriver in await scheduler.context.project.extensions
                else set()
            )
        )
