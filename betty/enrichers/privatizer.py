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

    Entities in Betty have privacy. This is a *ternary* property, with the following possible values:

    public (``entity.privacy = betty.privacy.Privacy.PUBLIC``)
        The entity will be included when publishing your ancestry. The privacy **should not** be changed.
    private (``entity.privacy = betty.privacy.Privacy.PRIVATE``)
        The entity will not be included when publishing your ancestry. The privacy **should not** be changed.
    undetermined (``entity.privacy = betty.privacy.Privacy.UNDETERMINED``)
        The entity is public, but its privacy **may** be determined or changed at will.

    The following entities are processed by the Privatizer. They are marked *private* except if any of the following
    conditions are met:

    People
      People are considered dead past the *lifetime threshold*, which
      :py:const:`defaults to 123 years <betty.project.default_lifetime_threshold>`, but can be changed in your
      project's :py:class:`configuration <betty.project.ProjectData>`.

      * The person has an end-of-life event, such as a death, final disposition, or will.
      * Any event that was at least the *lifetime threshold* ago.
      * For every person *n* generation(s) before this person, if that person has an end-of-life event at least *n* *
        *lifetime threshold* ago.
      * For every person *n* generation(s) before this person, if that person has any event that was at least (*n* + 1) *
        *lifetime threshold* ago.
      * For every descendant if that person has any event that was at least *lifetime threshold* ago.

      If the Privatizer determines a person private, it will also privatize any events, citations, and files associated
      with that person.

    File
      Any citations associated with private files will be privatized.

    Event
      Any citations and files associated with private events will be privatized.

    Citation
      The source and any files associated with private citations will be privatized.

    Source
      Any files associated with private sources will be privatized.

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
                if Deriver in self._project.service_providers
                else set(),
                project=self._project,
            )
        )
