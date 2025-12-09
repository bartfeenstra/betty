"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.locale.localizable.gettext import _
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.deriver.jobs import DeriveAncestry
from betty.project.factory import ProjectDependentSelfFactory
from betty.project.load import PostLoader

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext


@final
@ExtensionDefinition(
    "deriver",
    label="Deriver",
    description=_(
        "Create events such as births and deaths by deriving their details from existing information."
    ),
)
class Deriver(PostLoader, ProjectDependentSelfFactory, Extension):
    """
    Expand an ancestry by deriving additional data from existing data.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(DeriveAncestry())
