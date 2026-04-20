"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.factory import Manufacturable
from betty.load import Enricher, EnricherDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.enricher.deriver.jobs import DeriveAncestry
from betty.project import Project

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@EnricherDefinition(
    "deriver",
    label="Deriver",
    description=_(
        "Create events such as births and deaths by deriving their details from existing information."
    ),
)
class Deriver(Enricher, Manufacturable):
    """
    .. plugin:: enricher:deriver.

    The ``deriver`` extension derives, or infers, events for people based on their existing events. For example, we know that someone's
    final disposition, such as a burial or cremation, comes after their death. If a person has a *burial* event without a
    date, and a *death* event with a date of *January 1, 1970*, the Deriver will update the *burial* event with the date
    range *sometime after January 1, 1970*.

    The Deriver works for every event type that declares it can be derived, and depending on which other event
    types it declares it comes before or after. This means that the behavior of this extension is complex, and dependent on
    the event types used within your site as well as the existing events for each person.
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
    async def enrich(self, scheduler: Scheduler) -> None:
        await scheduler.add(DeriveAncestry(project=self._project))
