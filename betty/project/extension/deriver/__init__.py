"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.project.extension import Extension, ExtensionPlugin
from betty.project.extension.deriver.jobs import DeriveAncestry
from betty.project.load import PostLoader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext


@final
@ExtensionPlugin(
    id="deriver",
    label="Deriver",
    description=_(
        "Create events such as births and deaths by deriving their details from existing information."
    ),
)
class Deriver(PostLoader, Extension):
    """
    Expand an ancestry by deriving additional data from existing data.
    """

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(DeriveAncestry())
