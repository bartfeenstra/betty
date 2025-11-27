"""
Jobs.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.person import Person
from betty.job import Job
from betty.locale.localizable import _, ngettext
from betty.privacy import HasPrivacy
from betty.project import ProjectContext

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence

    from betty.job.scheduler import Scheduler
    from betty.machine_name import MachineName
    from betty.model import Entity


class PrivatizeAncestry(Job[ProjectContext]):
    """
    Privatize an ancestry.
    """

    def __init__(self, dependencies: set[str] | None = None):
        super().__init__(self.id_for(), dependencies=dependencies)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "privatizer:privatize"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        await project.app.localizer
        user = project.app.user

        newly_privatized: MutableMapping[MachineName, int] = defaultdict(lambda: 0)
        entities: MutableSequence[HasPrivacy & Entity] = []
        for entity in project.ancestry:
            if isinstance(entity, HasPrivacy):
                entities.append(entity)
                if entity.private:
                    newly_privatized[entity.plugin.id] -= 1

        for entity in entities:
            await project.privatizer.privatize(entity)

        for entity in entities:
            if entity.private:
                newly_privatized[entity.plugin.id] += 1

        if newly_privatized[Person.plugin.id] > 0:
            await user.message_information_details(
                _(
                    "Privatized {count} people because they are likely still alive."
                ).format(
                    count=str(newly_privatized[Person.plugin.id]),
                )
            )
        for entity_type_id in set(newly_privatized) - {Person.plugin.id}:
            if newly_privatized[entity_type_id] > 0:
                await user.message_information_details(
                    ngettext(
                        'Privatized {count} "{entity_type_id}" entity, because it is associated with private information.',
                        'Privatized {count} "{entity_type_id}" entities, because they are associated with private information.',
                        newly_privatized[entity_type_id],
                    ).format(
                        entity_type_id=entity_type_id,
                    )
                )
