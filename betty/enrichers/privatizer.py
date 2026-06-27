"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.enrichers.deriver import Deriver
from betty.factory import Manufacturable
from betty.jobs.derive_ancestry import DeriveAncestry
from betty.jobs.privatize_ancestry import PrivatizeAncestry
from betty.load import Enricher, EnricherDefinition
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@EnricherDefinition(
    "privatizer",
    label="Privatizer",
    description=_(
        "Determine if people can be proven to have died. If not, mark them and their associated entities private."
    ),
)
class Privatizer(Enricher, Manufacturable):
    """
    .. plugin:: enricher:privatizer.
    """

    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def enrich(self, scheduler: Scheduler, /) -> None:
        await scheduler.add(
            PrivatizeAncestry(
                dependencies={DeriveAncestry.id_for()}
                if Deriver in self._project.extensions
                else set(),
                project=self._project,
            )
        )
