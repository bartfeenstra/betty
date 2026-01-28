"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.extension import Extension, ExtensionDefinition
from betty.extension.deriver import Deriver
from betty.extension.deriver.jobs import DeriveAncestry
from betty.extension.privatizer.jobs import PrivatizeAncestry
from betty.locale.localizable.gettext import _
from betty.project.factory import require_project
from betty.project.load import PostLoader
from betty.service.level.factory import ServiceLevelDependentSelfFactory

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project
    from betty.project.job import ProjectContext


@final
@ExtensionDefinition(
    "privatizer",
    label="Privatizer",
    description=_(
        "Determine if people can be proven to have died. If not, mark them and their associated entities private."
    ),
    comes_after={Deriver},
)
class Privatizer(PostLoader, ServiceLevelDependentSelfFactory, Extension):
    """
    .. plugin:: extension:privatizer.

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
      :py:const:`defaults to 123 years <betty.project.config.DEFAULT_LIFETIME_THRESHOLD>`, but can be changed in your
      project's :py:class:`configuration <betty.project.config.ProjectConfiguration>`.

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

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(
            PrivatizeAncestry(
                dependencies={DeriveAncestry.id_for()}
                if Deriver.plugin().id in await scheduler.context.project.extensions
                else set()
            )
        )
