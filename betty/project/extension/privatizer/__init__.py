"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import Plain, _
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.deriver import Deriver
from betty.project.extension.deriver.jobs import DeriveAncestry
from betty.project.extension.privatizer.jobs import PrivatizeAncestry
from betty.project.load import PostLoader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext


@final
@ExtensionDefinition(
    id="privatizer",
    label=Plain("Privatizer"),
    description=_(
        "Determine if people can be proven to have died. If not, mark them and their associated entities private."
    ),
    comes_after={Deriver.plugin},
)
class Privatizer(PostLoader, Extension):
    """
    Extend the Betty Application with privatization features.
    """

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(
            PrivatizeAncestry(
                dependencies={DeriveAncestry.id_for()}
                if Deriver.plugin.id in await scheduler.context.project.extensions
                else set()
            )
        )
